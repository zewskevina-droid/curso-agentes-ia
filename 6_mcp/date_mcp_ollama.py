import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import date
from urllib.error import URLError
from urllib.request import Request, urlopen

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("date_server")


@mcp.tool()
async def get_today_date() -> str:
    """Return today's date in ISO format, YYYY-MM-DD."""
    return date.today().isoformat()


def call_ollama(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Call Ollama through its OpenAI-compatible chat API."""
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    host = get_ollama_host().rstrip("/")
    payload = {
        "model": model,
        "messages": messages,
    }
    if tools:
        payload["tools"] = tools

    request = Request(
        f"{host}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {host}. Make sure Ollama is running on "
            f"Windows and the model exists, for example: `ollama pull {model}`."
        ) from exc


def get_ollama_host() -> str:
    """Return Ollama's base URL, using the Windows host when running in WSL."""
    if os.getenv("OLLAMA_HOST"):
        return os.getenv("OLLAMA_HOST", "")

    try:
        windows_host = subprocess.check_output(
            "ip route | awk '/default/ {print $3}'",
            shell=True,
            text=True,
        ).strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        windows_host = ""

    if windows_host:
        return f"http://{windows_host}:11434"
    return "http://localhost:11434"


def mcp_tool_to_ollama_tool(tool) -> dict:
    """Convert one MCP tool description to Ollama's tool-calling format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def tool_result_text(result) -> str:
    """Extract text from an MCP CallToolResult."""
    parts = []
    for item in result.content:
        text = getattr(item, "text", None)
        if text is not None:
            parts.append(text)
        else:
            parts.append(str(item))
    return "\n".join(parts)


async def run_client(question: str) -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.abspath(__file__), "--server"],
    )

    async with stdio_client(server_params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = [mcp_tool_to_ollama_tool(tool) for tool in tools_result.tools]
            print("MCP tools available:", [tool["function"]["name"] for tool in tools])
            print("Using Ollama at:", f"{get_ollama_host().rstrip('/')}/v1")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. When the user asks for today's "
                        "date, use the available tool instead of guessing."
                    ),
                },
                {"role": "user", "content": question},
            ]

            try:
                response = call_ollama(messages, tools)
            except RuntimeError as exc:
                print(exc)
                return

            assistant_message = response["choices"][0]["message"]
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls", [])
            if not tool_calls:
                print("\nOllama response:")
                print(assistant_message.get("content", ""))
                return

            for tool_call in tool_calls:
                function = tool_call["function"]
                tool_name = function["name"]
                arguments = function.get("arguments") or {}
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)

                print(f"Calling MCP tool: {tool_name}({arguments})")
                result = await session.call_tool(tool_name, arguments=arguments)
                result_text = tool_result_text(result)
                print(f"MCP result: {result_text}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", tool_name),
                        "name": tool_name,
                        "content": result_text,
                    }
                )

            try:
                final_response = call_ollama(messages, tools)
            except RuntimeError as exc:
                print(exc)
                return

            print("\nOllama response:")
            print(final_response["choices"][0]["message"]["content"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MCP date server plus an Ollama MCP client demo."
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run only the MCP server over stdio.",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="What is today's date? Use the MCP tool.",
        help="Question to ask Ollama.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.server:
        mcp.run(transport="stdio")
    else:
        asyncio.run(run_client(args.question))

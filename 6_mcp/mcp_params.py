import os
from dotenv import load_dotenv
from market import is_paid_polygon, is_realtime_polygon

load_dotenv(override=True)

polygon_api_key = os.getenv("POLYGON_API_KEY")

# Servidor MCP para que el trader lea datos de mercado

if is_paid_polygon or is_realtime_polygon:
    market_mcp = {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/polygon-io/mcp_polygon@v0.1.0", "mcp_polygon"],
        "env": {"POLYGON_API_KEY": polygon_api_key},
    }
else:
    market_mcp = {"command": "uv", "args": ["run", "market_server.py"]}


# Conjunto completo de servidores MCP para el trader: cuentas, notificaciones push y mercado

trader_mcp_server_params = [
    {"command": "uv", "args": ["run", "accounts_server.py"]},
    {"command": "uv", "args": ["run", "push_server.py"]},
    market_mcp,
]

# Conjunto completo de servidores MCP para el investigador: busqueda web, Fetch y memoria


def researcher_mcp_server_params(name: str):
    return [
        {"command": "uv", "args": ["run", "search_server.py"]},
        {"command": "uvx", "args": ["mcp-server-fetch"]},
        {
            "command": "npx",
            "args": ["-y", "mcp-memory-libsql"],
            "env": {"LIBSQL_URL": f"file:./memory/{name}.db"},
        },
    ]

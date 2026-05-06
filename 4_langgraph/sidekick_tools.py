from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import json
import os
from pathlib import Path
import re
import shutil
import textwrap
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper


load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()
SANDBOX_DIR = Path(__file__).resolve().parent / "sandbox"


# Funcion para obtener las herramientas de Playwright de forma asincrona
async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


# Herramienta de notificaciones push para el asistente
def push(text: str):
    """Send a push notification to the user"""
    requests.post(
        pushover_url,
        data={"token": pushover_token, "user": pushover_user, "message": text},
    )
    return "success"


# Herramientas de gestion de archivos para el asistente
def get_file_tools():
    toolkit = FileManagementToolkit(root_dir=str(SANDBOX_DIR))
    return toolkit.get_tools()


def _sandbox_path(file_name: str) -> Path:
    path = (SANDBOX_DIR / file_name.strip()).resolve()
    if not path.is_relative_to(SANDBOX_DIR.resolve()):
        raise ValueError("La ruta debe estar dentro de la carpeta sandbox")
    return path


def _clean_markdown_inline(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    text = text.replace("`", "")
    return text.strip()


def _markdown_to_lines(markdown: str) -> list[tuple[str, int, bool]]:
    lines = []
    in_code_block = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            lines.append(("", 11, False))
            continue

        if in_code_block:
            lines.append((line, 10, False))
            continue

        stripped = line.strip()
        if not stripped:
            lines.append(("", 11, False))
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            size = max(12, 22 - (level * 2))
            lines.append((_clean_markdown_inline(heading.group(2)), size, True))
            lines.append(("", 11, False))
            continue

        list_item = re.match(r"^([-*+]|\d+\.)\s+(.*)$", stripped)
        if list_item:
            lines.append((f"- {_clean_markdown_inline(list_item.group(2))}", 11, False))
            continue

        lines.append((_clean_markdown_inline(stripped), 11, False))

    return lines


def _escape_pdf_text(text: str) -> bytes:
    encoded = text.encode("latin-1", errors="replace")
    return encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _build_pdf(lines: list[tuple[str, int, bool]]) -> bytes:
    width, height = 595, 842
    margin_x, margin_y = 54, 52
    max_y = height - margin_y
    y = max_y
    pages: list[list[bytes]] = [[]]

    def new_page():
        nonlocal y
        pages.append([])
        y = max_y

    for text, size, bold in lines:
        if not text:
            y -= 13
            if y < margin_y:
                new_page()
            continue

        wrap_width = max(35, int((width - (2 * margin_x)) / (size * 0.52)))
        for part in textwrap.wrap(text, width=wrap_width) or [""]:
            line_height = int(size * 1.4)
            if y - line_height < margin_y:
                new_page()
            font = "F2" if bold else "F1"
            escaped_text = _escape_pdf_text(part)
            command = f"BT /{font} {size} Tf {margin_x} {y} Td (".encode("ascii")
            pages[-1].append(command + escaped_text + b") Tj ET\n")
            y -= line_height

        if bold:
            y -= 4

    objects: list[bytes] = [
        b"",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]
    page_numbers = []

    for page in pages:
        stream = b"".join(page)
        content = (
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        )
        content_number = len(objects) + 1
        objects.append(content)
        page_number = len(objects) + 1
        page_numbers.append(page_number)
        page_object = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            f"/Contents {content_number} 0 R >>"
        ).encode("ascii")
        objects.append(page_object)

    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_numbers)} >>".encode("ascii")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return bytes(pdf)


def markdown_to_pdf(text: str):
    """Convert a markdown file from sandbox into a PDF file."""
    parts = [part.strip() for part in re.split(r"\s*(?:->|\|)\s*", text, maxsplit=1)]
    markdown_file = parts[0]
    if not markdown_file:
        return "Error: indica el archivo Markdown, por ejemplo dinner.md"

    input_path = _sandbox_path(markdown_file)
    if input_path.suffix.lower() != ".md":
        return "Error: el archivo de entrada debe tener extension .md"
    if not input_path.exists():
        return f"Error: no existe {markdown_file} en sandbox"

    if len(parts) > 1 and parts[1]:
        output_path = _sandbox_path(parts[1])
    else:
        output_path = input_path.with_suffix(".pdf")
    if output_path.suffix.lower() != ".pdf":
        output_path = output_path.with_suffix(".pdf")

    markdown = input_path.read_text(encoding="utf-8")
    pdf = _build_pdf(_markdown_to_lines(markdown))
    output_path.write_bytes(pdf)
    return f"PDF creado: {output_path.name}"


def _pc_path(path_text: str) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(path_text.strip()))
    return Path(expanded).resolve()


def _protected_delete_path(path: Path) -> bool:
    protected_paths = {
        Path(path.anchor).resolve(),
        Path.home().resolve(),
        Path.cwd().resolve(),
    }
    return path in protected_paths


def _parse_file_operation(text: str) -> dict:
    try:
        operation = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Entrada invalida. Usa JSON, por ejemplo: "
            '{"action":"copy","source":"C:/origen.txt","destination":"C:/destino.txt"}'
        ) from exc

    if not isinstance(operation, dict):
        raise ValueError("La entrada debe ser un objeto JSON")
    return operation


def pc_file_manager(text: str):
    """Copy, move, or delete files and folders on the local PC."""
    try:
        operation = _parse_file_operation(text)
        action = str(operation.get("action", "")).lower().strip()
        source_text = operation.get("source")
        destination_text = operation.get("destination")
        overwrite = bool(operation.get("overwrite", False))
        recursive = bool(operation.get("recursive", False))

        if action not in {"copy", "move", "delete"}:
            return "Error: action debe ser copy, move o delete"
        if not source_text:
            return "Error: falta source"

        source = _pc_path(str(source_text))
        if not source.exists():
            return f"Error: no existe source: {source}"

        if action in {"copy", "move"}:
            if not destination_text:
                return "Error: falta destination"

            destination = _pc_path(str(destination_text))
            if destination.exists() and not overwrite:
                return f"Error: destination ya existe: {destination}. Usa overwrite=true si quieres reemplazarlo."

            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and overwrite:
                if destination.is_dir():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()

            if action == "copy":
                if source.is_dir():
                    shutil.copytree(source, destination)
                else:
                    shutil.copy2(source, destination)
                return f"Copiado: {source} -> {destination}"

            shutil.move(str(source), str(destination))
            return f"Movido: {source} -> {destination}"

        if not operation.get("confirm"):
            return 'Error: para eliminar debes incluir "confirm": true'
        if _protected_delete_path(source):
            return f"Error: no se permite eliminar esta ruta protegida: {source}"

        if source.is_dir():
            if not recursive:
                return 'Error: para eliminar carpetas debes incluir "recursive": true'
            if operation.get("confirm_text") != "DELETE":
                return 'Error: para eliminar carpetas debes incluir "confirm_text": "DELETE"'
            shutil.rmtree(source)
        else:
            source.unlink()
        return f"Eliminado: {source}"
    except Exception as exc:
        return f"Error: {exc}"


# Funcion para obtener otras herramientas asincronas
async def other_tools():
    push_tool = Tool(
        name="send_push_notification",
        func=push,
        description="Utiliza esta herramienta cuando quieras enviar una notificacion push",
    )
    file_tools = get_file_tools()
    markdown_to_pdf_tool = Tool(
        name="markdown_to_pdf",
        func=markdown_to_pdf,
        description=(
            "Convierte un archivo Markdown de la carpeta sandbox a PDF. "
            "Entrada: 'archivo.md' o 'archivo.md -> salida.pdf'."
        ),
    )
    pc_file_manager_tool = Tool(
        name="pc_file_manager",
        func=pc_file_manager,
        description=(
            "Gestiona archivos y carpetas en la PC local: copy, move y delete. "
            "La entrada debe ser JSON. Ejemplos: "
            '{"action":"copy","source":"C:/origen.txt","destination":"C:/destino.txt"}; '
            '{"action":"move","source":"C:/origen.txt","destination":"C:/carpeta/origen.txt"}; '
            '{"action":"delete","source":"C:/archivo.txt","confirm":true}. '
            'Para eliminar carpetas usa tambien "recursive": true y "confirm_text": "DELETE".'
        ),
    )

    tool_search = Tool(
        name="search",
        func=serper.run,
        description="Utiliza esta herramienta cuando quieras obtener los resultados de una busqueda en la web",
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    # Herramienta de REPL de Python para el asistente.
    python_repl = PythonREPLTool()

    return file_tools + [
        push_tool,
        markdown_to_pdf_tool,
        pc_file_manager_tool,
        tool_search,
        python_repl,
        wiki_tool,
    ]

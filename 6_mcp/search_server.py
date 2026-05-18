from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("search_server")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo HTML search.

    Args:
        query: Search query.
        max_results: Maximum number of results to return.
    """
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    response = requests.get(url, headers=HEADERS, timeout=30)
    if not response.ok:
        return f"Busqueda fallo con HTTP {response.status_code}: {response.text[:500]}"

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for result in soup.select(".result"):
        title_el = result.select_one(".result__title a")
        snippet_el = result.select_one(".result__snippet")
        if not title_el:
            continue

        title = title_el.get_text(" ", strip=True)
        link = title_el.get("href", "")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
        results.append(f"- {title}\n  URL: {link}\n  Resumen: {snippet}")

        if len(results) >= max_results:
            break

    if not results:
        return f"No encontre resultados para: {query}"

    return f"Resultados de busqueda para: {query}\n\n" + "\n".join(results)


@mcp.tool()
def fetch_page(url: str, max_chars: int = 8000) -> str:
    """Fetch and summarize visible text from a web page.

    Args:
        url: URL to fetch.
        max_chars: Maximum characters to return.
    """
    response = requests.get(url, headers=HEADERS, timeout=30)
    if not response.ok:
        return f"No pude leer {url}. HTTP {response.status_code}: {response.text[:500]}"

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else url
    text = soup.get_text("\n", strip=True)
    text = "\n".join(line for line in text.splitlines() if line.strip())

    return f"Titulo: {title}\nURL: {urljoin(url, response.url)}\n\n{text[:max_chars]}"


if __name__ == "__main__":
    mcp.run(transport="stdio")

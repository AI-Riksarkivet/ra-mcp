"""MCP tool definitions for the PDF Viewer."""

import base64
import logging
from pathlib import Path
from typing import Annotated
from urllib.parse import unquote, urlparse
from uuid import uuid4

from fastmcp import Context
from fastmcp.server.apps import UI_EXTENSION_ID, AppConfig, ResourceCSP
from fastmcp.tools import ToolResult
from mcp import types
from pydantic import Field

from ra_mcp_pdf_mcp import pdf_mcp as mcp
from ra_mcp_pdf_mcp.cache import (
    CHUNK_SIZE,
    blocks_cache,
    read_pdf_range,
    schedule_prefetch,
)
from ra_mcp_pdf_mcp.models import PdfViewerState
from ra_mcp_pdf_mcp.search import search_pages
from ra_mcp_pdf_mcp.state import (
    get_active_state,
    get_state,
    put_state,
)


logger = logging.getLogger("ra_mcp.pdf.tools")

DIST_DIR = Path(__file__).parent / "dist"
RESOURCE_URI = "ui://pdf-viewer/mcp-app.html"
DEFAULT_PDF = "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/216090389-e30a88-medeltidens-samhalle.pdf?download=true"


def _text_result(text: str) -> ToolResult:
    return ToolResult(content=[types.TextContent(type="text", text=text)])


def _error_result(text: str) -> ToolResult:
    return ToolResult(content=[types.TextContent(type="text", text=f"Error: {text}")])


# ---------------------------------------------------------------------------
# display_pdf
# ---------------------------------------------------------------------------


@mcp.tool(
    name="display_pdf",
    description=(
        "Display an interactive PDF viewer with search, navigation, and annotation support. "
        "Accepts a URL to a PDF file. After displaying, the current page text is sent via model context. "
        "Use search_pdf to search text across ALL pages of the PDF. "
        "The viewer supports zoom, page navigation, text search, text selection, and annotations."
    ),
    app=AppConfig(resource_uri=RESOURCE_URI),
)
async def display_pdf(
    url: Annotated[str, Field(description="URL to a PDF file. Supports direct links and academic sources (arxiv, etc).")] = DEFAULT_PDF,
    title: Annotated[str | None, Field(description="Optional display title for the PDF.")] = None,
    ctx: Context | None = None,
) -> ToolResult:
    """Display an interactive PDF viewer."""
    if not url:
        return _error_result("No URL provided.")

    display_title = title or _extract_title(url)
    view_id = str(uuid4())

    state = PdfViewerState(
        view_id=view_id,
        url=url,
        title=display_title,
        source_url=url,
    )
    sc = await put_state(state)

    schedule_prefetch(url)

    has_ui = ctx.client_supports_extension(UI_EXTENSION_ID) if ctx else False
    summary_parts = [
        f"Displaying PDF: {display_title}",
        f"view_uuid: {view_id}",
        "",
        "Use pdf_set_search to highlight text, pdf_go_to_page to navigate, search_pdf to search all pages.",
    ]
    if not has_ui:
        summary_parts.insert(1, f"URL: {url}")
    summary = "\n".join(summary_parts)

    logger.info("display_pdf: url=%s, view_id=%s", url, view_id)
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content=sc,
    )


# ---------------------------------------------------------------------------
# read_pdf_bytes — chunked streaming (app-visible only)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="read_pdf_bytes",
    description="Read a range of bytes from a PDF file (max 4MB per request). Used by the viewer to stream PDF data.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def read_pdf_bytes(
    url: Annotated[str, Field(description="URL of the PDF file.")],
    offset: Annotated[int, Field(description="Byte offset to start reading from.", ge=0)] = 0,
) -> ToolResult:
    """Stream PDF data in chunks with pagination metadata."""
    try:
        chunk, total_bytes = await read_pdf_range(url, offset, CHUNK_SIZE)
    except Exception as e:
        logger.error("read_pdf_bytes: failed to fetch %s: %s", url, e)
        return _error_result(f"Failed to fetch PDF: {e}")

    byte_count = len(chunk)
    end = offset + byte_count
    has_more = total_bytes > 0 and end < total_bytes
    chunk_b64 = base64.b64encode(chunk).decode("ascii")

    return ToolResult(
        content=[types.TextContent(type="text", text=f"Read {byte_count} bytes ({offset}-{end}/{total_bytes})")],
        structured_content={
            "bytes": chunk_b64,
            "offset": offset,
            "byteCount": byte_count,
            "totalBytes": total_bytes,
            "hasMore": has_more,
        },
    )


# ---------------------------------------------------------------------------
# get_pdf_state — state polling (app-visible only)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_pdf_state",
    description="Get the current PDF viewer state by view_id. Used by the viewer to poll for LLM-initiated changes.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def get_pdf_state(
    view_id: Annotated[str, Field(description="View ID from the initial tool result.")],
) -> ToolResult:
    state = await get_state(view_id)
    return ToolResult(
        content=[types.TextContent(type="text", text=f"PDF state v{state.version}")],
        structured_content=state.model_dump(),
    )


# ---------------------------------------------------------------------------
# get_page_blocks — block overlay data (app-visible only)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_page_blocks",
    description="Get all structured blocks for a page with bounding boxes and types. Used by the viewer for block overlay.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def get_page_blocks(
    url: Annotated[str, Field(description="URL of the PDF.")],
    page: Annotated[int, Field(description="Page number (1-based).", ge=1)],
) -> ToolResult:
    """Return all blocks for a page with bbox and block_type for overlay rendering."""
    if url not in blocks_cache:
        return _error_result("PDF not loaded.")

    pages = blocks_cache[url]
    page_idx = page - 1
    if page_idx < 0 or page_idx >= len(pages):
        return _error_result(f"Page {page} out of range (1-{len(pages)}).")

    page_data = pages[page_idx]
    page_bbox = page_data.get("bbox", [0, 0, 0, 0])

    blocks = [{"bbox": block.get("bbox", [0, 0, 0, 0]), "blockType": block.get("block_type", "")} for block in page_data.get("children", [])]

    return ToolResult(
        content=[types.TextContent(type="text", text=f"Page {page}: {len(blocks)} blocks")],
        structured_content={"pageBbox": page_bbox, "blocks": blocks},
    )


# ---------------------------------------------------------------------------
# read_pdf_page — on-demand page text for model context
# ---------------------------------------------------------------------------


@mcp.tool(
    name="read_pdf_page",
    description=(
        "Read the text content of a specific page from a loaded PDF. "
        "Use this to read what's on a page after navigating with pdf_go_to_page, "
        "or to read pages referenced in search_pdf results."
    ),
)
async def read_pdf_page(
    url: Annotated[str, Field(description="URL of the PDF (must match a previous display_pdf call).")],
    page: Annotated[int, Field(description="Page number (1-based).", ge=1)],
) -> ToolResult:
    """Return structured text blocks for a specific page from the cached JSON."""
    if url not in blocks_cache:
        return _error_result("PDF not loaded. Use display_pdf first.")

    pages = blocks_cache[url]
    page_idx = page - 1
    if page_idx < 0 or page_idx >= len(pages):
        return _error_result(f"Page {page} out of range (1-{len(pages)}).")

    page_data = pages[page_idx]
    from ra_mcp_pdf_mcp.search import html_to_text

    lines: list[str] = []
    for block in page_data.get("children", []):
        html = block.get("html", "")
        if not html:
            continue
        block_type = block.get("block_type", "")
        text = html_to_text(html)
        if not text:
            continue
        if block_type == "SectionHeader":
            lines.append(f"\n## {text}")
        elif block_type in ("PageHeader", "PageFooter"):
            continue  # skip headers/footers
        else:
            lines.append(text)

    page_text = "\n\n".join(lines).strip()
    return _text_result(f"Page {page}/{len(pages)}:\n\n{page_text}")


# ---------------------------------------------------------------------------
# State-mutation tools (no AppConfig — reuse existing viewer)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="pdf_set_search",
    description=(
        "Set the search/highlight term in the already-open PDF viewer. "
        "The viewer will highlight all occurrences on the current page. "
        "Use after display_pdf when the user wants to find or highlight text."
    ),
)
async def pdf_set_search(
    search_term: Annotated[str, Field(description="Search term to highlight. Use empty string to clear.")],
) -> ToolResult:
    try:
        state = await get_active_state()
    except LookupError as e:
        return _error_result(str(e))

    state.search_term = search_term
    await put_state(state)

    action = f"Highlighting '{search_term}'" if search_term else "Cleared search"
    return _text_result(f"{action} in the PDF viewer.")


@mcp.tool(
    name="pdf_go_to_page",
    description="Navigate the already-open PDF viewer to a specific page. Does NOT replace the loaded PDF — just jumps to that page.",
)
async def pdf_go_to_page(
    page: Annotated[int, Field(description="Page number (1-based).")],
) -> ToolResult:
    try:
        state = await get_active_state()
    except LookupError as e:
        return _error_result(str(e))

    state.go_to_page = page - 1  # convert to 0-based
    await put_state(state)
    return _text_result(f"Navigated to page {page}.")


# ---------------------------------------------------------------------------
# list_pdfs
# ---------------------------------------------------------------------------


@mcp.tool(
    name="list_pdfs",
    description=(
        "List available PDF documents from Riksarkivet's collection. "
        "Includes guides on medieval history, Sami history, genealogy research, and more. "
        "Use display_pdf with the URL from the results to open a specific PDF."
    ),
)
async def list_pdfs() -> ToolResult:
    """Return the curated gallery of available PDFs."""
    from ra_mcp_pdf_mcp.gallery import get_gallery_items

    items = get_gallery_items()
    lines = [f"{len(items)} PDF guides available:\n"]
    for item in items:
        lines.append(f"- **{item['title']}**: {item['description']}")
        lines.append(f"  URL: {item['url']}")

    return ToolResult(
        content=[types.TextContent(type="text", text="\n".join(lines))],
        structured_content={"items": items},
    )


# ---------------------------------------------------------------------------
# search_pdf — DataLab block-level search
# ---------------------------------------------------------------------------


@mcp.tool(
    name="search_pdf",
    description=(
        "Search for text across ALL pages of a loaded PDF. Returns per-page match counts and total. "
        "Use after display_pdf to find where specific terms appear in the document. "
        "The URL must match the one used in display_pdf."
    ),
)
async def search_pdf(
    url: Annotated[str, Field(description="URL of the PDF file (must match a previous display_pdf call).")],
    term: Annotated[str, Field(description="The search term to find.")],
) -> ToolResult:
    """Search PDF pages using DataLab blocks (exact bbox, structured text)."""
    if not term or not term.strip():
        return ToolResult(
            content=[types.TextContent(type="text", text="No search term provided.")],
            structured_content={"pageMatches": [], "totalMatches": 0},
        )

    if url not in blocks_cache:
        return _error_result("PDF not yet loaded. Use display_pdf first.")

    result = search_pages(blocks_cache[url], term.strip())
    return ToolResult(
        content=[types.TextContent(type="text", text=result.summary(term.strip()))],
        structured_content=result.to_structured(),
    )


# ---------------------------------------------------------------------------
# UI Resource
# ---------------------------------------------------------------------------

_PDF_DOMAINS = [
    "https://huggingface.co",
    "https://cas-bridge.xethub-eu.hf.co",
    "https://cas-bridge.xethub.hf.co",
    "https://cdn-lfs.huggingface.co",
    "https://cdn-lfs-us-1.huggingface.co",
    "https://cdn-lfs-eu-1.huggingface.co",
]

_resource_csp = ResourceCSP(connectDomains=_PDF_DOMAINS)


@mcp.resource(uri=RESOURCE_URI, app=AppConfig(csp=_resource_csp))
def get_ui_resource() -> str:
    html_path = DIST_DIR / "mcp-app.html"
    if not html_path.exists():
        msg = f"UI resource not found: {html_path}"
        raise FileNotFoundError(msg)
    return html_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_title(url: str) -> str:
    """Extract a display title from a URL."""
    path = urlparse(url).path
    filename = unquote(path.rsplit("/", 1)[-1])
    if filename.lower().endswith(".pdf"):
        filename = filename[:-4]
    return filename or "Document"

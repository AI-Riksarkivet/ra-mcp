"""PDF Viewer MCP tools — display PDFs, navigate, search, annotate."""

import base64
import logging
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import httpx
from fastmcp import Context
from fastmcp.server.apps import UI_EXTENSION_ID, AppConfig
from fastmcp.tools import ToolResult
from mcp import types
from pydantic import Field

from ra_mcp_pdf_mcp import pdf_mcp as mcp
from ra_mcp_pdf_mcp.models import PdfCommand, PdfViewerState
from ra_mcp_pdf_mcp.state import (
    dequeue_commands,
    enqueue_command,
    get_state,
    put_state,
)


logger = logging.getLogger("ra_mcp.pdf.tools")

DIST_DIR = Path(__file__).parent / "dist"
RESOURCE_URI = "ui://pdf-viewer/mcp-app.html"

# Chunk size for streaming PDF bytes (512 KB)
CHUNK_SIZE = 512 * 1024
# Max PDF size for caching (50 MB)
MAX_PDF_SIZE = 50 * 1024 * 1024

# In-memory PDF cache: url → bytes
_pdf_cache: dict[str, bytes] = {}

DEFAULT_PDF = "https://filer.riksarkivet.se/nedladdningsbara-filer/Hur%20riket%20styrdes_63MB.pdf"


def _text_result(text: str) -> ToolResult:
    return ToolResult(content=[types.TextContent(type="text", text=text)])


def _error_result(text: str) -> ToolResult:
    return ToolResult(content=[types.TextContent(type="text", text=text)], is_error=True)


# ---------------------------------------------------------------------------
# display_pdf — main entry point
# ---------------------------------------------------------------------------


@mcp.tool(
    name="display_pdf",
    description=(
        "Display an interactive PDF viewer with search, navigation, and annotation support. "
        "Accepts a URL to a PDF file. Supported sources: direct PDF URLs, arxiv.org, "
        "biorxiv.org, riksarkivet.se, and other academic sources. "
        "The viewer supports zoom, page navigation, text search, text selection, "
        "and annotation (highlights, notes, stamps, etc.)."
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

    has_ui = ctx.client_supports_extension(UI_EXTENSION_ID) if ctx else False
    summary = f"Displaying PDF: {display_title}"
    if not has_ui:
        summary += f"\nURL: {url}"

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
    description="Read a range of bytes from a PDF file (max 512KB per request). Used by the viewer to stream PDF data.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def read_pdf_bytes(
    url: Annotated[str, Field(description="URL of the PDF file.")],
    offset: Annotated[int, Field(description="Byte offset to start reading from.", ge=0)] = 0,
) -> ToolResult:
    """Stream PDF data in chunks with pagination metadata."""
    try:
        pdf_bytes = await _fetch_pdf(url)
    except Exception as e:
        logger.error("read_pdf_bytes: failed to fetch %s: %s", url, e)
        return _error_result(f"Failed to fetch PDF: {e}")

    total_bytes = len(pdf_bytes)
    end = min(offset + CHUNK_SIZE, total_bytes)
    chunk = pdf_bytes[offset:end]
    has_more = end < total_bytes

    chunk_b64 = base64.b64encode(chunk).decode("ascii")

    return ToolResult(
        content=[types.TextContent(type="text", text=f"Read {len(chunk)} bytes ({offset}-{end}/{total_bytes})")],
        structured_content={
            "bytes": chunk_b64,
            "offset": offset,
            "byteCount": len(chunk),
            "totalBytes": total_bytes,
            "hasMore": has_more,
        },
    )


# ---------------------------------------------------------------------------
# interact — model sends commands to the viewer
# ---------------------------------------------------------------------------


@mcp.tool(
    name="interact",
    description=(
        "Send commands to the active PDF viewer. Actions:\n"
        "- navigate: Go to a page. Requires `page` (1-based).\n"
        "- search: Search for text. Requires `query`.\n"
        "- zoom: Set zoom level. Requires `scale` (e.g. 1.5).\n"
        "- add_annotations: Add annotations. Requires `annotations` array.\n"
        "- remove_annotations: Remove annotations by ID. Requires `ids` array.\n"
        "- highlight_text: Find and highlight text. Requires `query`, optional `page`, `color`, `content`.\n"
        "- get_text: Extract text from page ranges. Requires `intervals` [{start, end}].\n"
        "- get_screenshot: Take page screenshot. Requires `page`.\n"
        "- fill_form: Fill form fields. Requires `fields` [{name, value}].\n"
    ),
)
async def interact(
    view_uuid: Annotated[str, Field(description="View UUID from the display_pdf result.")],
    action: Annotated[
        str,
        Field(
            description="Action to perform: navigate, search, zoom, add_annotations, remove_annotations, highlight_text, get_text, get_screenshot, fill_form."
        ),
    ],
    page: Annotated[int | None, Field(description="Page number (1-based) for navigate/get_screenshot.")] = None,
    query: Annotated[str | None, Field(description="Search query for search/highlight_text.")] = None,
    scale: Annotated[float | None, Field(description="Zoom scale for zoom action.")] = None,
    annotations: Annotated[list[dict] | None, Field(description="Annotation definitions for add_annotations.")] = None,  # type: ignore[type-arg]
    ids: Annotated[list[str] | None, Field(description="Annotation IDs for remove_annotations.")] = None,
    intervals: Annotated[list[dict] | None, Field(description="Page intervals [{start, end}] for get_text.")] = None,  # type: ignore[type-arg]
    fields: Annotated[list[dict] | None, Field(description="Form fields [{name, value}] for fill_form.")] = None,  # type: ignore[type-arg]
    color: Annotated[str | None, Field(description="Color for highlight_text.")] = None,
    content: Annotated[str | None, Field(description="Content/note for highlight_text.")] = None,
) -> ToolResult:
    """Send a command to the PDF viewer."""
    # Validate required params per action
    if action == "navigate" and page is None:
        return _error_result("navigate requires `page` parameter.")
    if action in ("search", "highlight_text") and not query:
        return _error_result(f"{action} requires `query` parameter.")
    if action == "zoom" and scale is None:
        return _error_result("zoom requires `scale` parameter.")
    if action == "add_annotations" and not annotations:
        return _error_result("add_annotations requires `annotations` parameter.")
    if action == "remove_annotations" and not ids:
        return _error_result("remove_annotations requires `ids` parameter.")
    if action == "fill_form" and not fields:
        return _error_result("fill_form requires `fields` parameter.")

    cmd = PdfCommand(
        type=action if action != "highlight_text" else "highlight_text",
        page=page,
        query=query,
        scale=scale,
        annotations=annotations,
        ids=ids,
        intervals=intervals,
        fields=fields,
        color=color,
        content=content,
        id=str(uuid4()) if action == "highlight_text" else None,
    )

    enqueue_command(view_uuid, cmd)

    # Build human-readable confirmation
    msg = _describe_action(action, page=page, query=query, scale=scale, annotations=annotations, ids=ids, fields=fields)
    logger.info("interact: view=%s action=%s", view_uuid, action)
    return _text_result(f"Queued: {msg}")


# ---------------------------------------------------------------------------
# poll_pdf_commands — viewer polls for commands (app-visible only)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="poll_pdf_commands",
    description="Poll for pending commands from the model. Used by the viewer to receive navigate/search/annotate commands.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def poll_pdf_commands(
    view_uuid: Annotated[str, Field(description="View UUID to poll commands for.")],
) -> ToolResult:
    """Long-poll for commands. Returns when commands are available or after timeout."""
    commands = await dequeue_commands(view_uuid, timeout=30.0)
    return ToolResult(
        content=[types.TextContent(type="text", text=f"{len(commands)} command(s)")],
        structured_content={"commands": commands},
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
# UI Resource
# ---------------------------------------------------------------------------


@mcp.resource(uri=RESOURCE_URI)
def get_ui_resource() -> str:
    html_path = DIST_DIR / "mcp-app.html"
    if not html_path.exists():
        msg = f"UI resource not found: {html_path}"
        raise FileNotFoundError(msg)
    return html_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _fetch_pdf(url: str) -> bytes:
    """Fetch a PDF and cache it in memory."""
    if url in _pdf_cache:
        return _pdf_cache[url]

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=120.0), follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    data = resp.content
    if len(data) > MAX_PDF_SIZE:
        msg = f"PDF too large to cache: {len(data)} bytes (max {MAX_PDF_SIZE})"
        raise ValueError(msg)

    _pdf_cache[url] = data
    return data


def _extract_title(url: str) -> str:
    """Extract a display title from a URL."""
    from urllib.parse import unquote, urlparse

    path = urlparse(url).path
    filename = unquote(path.rsplit("/", 1)[-1])
    if filename.lower().endswith(".pdf"):
        filename = filename[:-4]
    return filename or "Document"


def _describe_action(
    action: str,
    *,
    page: int | None = None,
    query: str | None = None,
    scale: float | None = None,
    annotations: list | None = None,
    ids: list | None = None,
    fields: list | None = None,
) -> str:
    """Build a human-readable description of an interact action."""
    match action:
        case "navigate":
            return f"Navigate to page {page}"
        case "search":
            return f"Search for '{query}'"
        case "zoom":
            return f"Zoom to {scale}x"
        case "add_annotations":
            return f"Add {len(annotations or [])} annotation(s)"
        case "remove_annotations":
            return f"Remove {len(ids or [])} annotation(s)"
        case "highlight_text":
            return f"Highlight '{query}'"
        case "get_text":
            return "Extract text"
        case "get_screenshot":
            return f"Screenshot page {page}"
        case "fill_form":
            return f"Fill {len(fields or [])} field(s)"
        case _:
            return action

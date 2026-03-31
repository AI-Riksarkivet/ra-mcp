"""PDF Viewer MCP tools — display PDFs, navigate, search, annotate."""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import httpx
from fastmcp import Context
from fastmcp.server.apps import UI_EXTENSION_ID, AppConfig, ResourceCSP
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

# Chunk size for streaming PDF bytes (4 MB — larger chunks = fewer round-trips)
CHUNK_SIZE = 8 * 1024 * 1024
# Max PDF size for caching (200 MB)
MAX_PDF_SIZE = 200 * 1024 * 1024

# In-memory PDF cache: url → bytes
_pdf_cache: dict[str, bytes] = {}
_background_tasks: set[asyncio.Task] = set()  # prevent GC of fire-and-forget tasks

DEFAULT_PDF = "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/Hur%20riket%20styrdes_63MB.pdf?download=true"


def _text_result(text: str) -> ToolResult:
    return ToolResult(content=[types.TextContent(type="text", text=text)])


def _error_result(text: str) -> ToolResult:
    return ToolResult(content=[types.TextContent(type="text", text=f"Error: {text}")])


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

    # Pre-fetch full PDF in background for search_pdf cache warmth.
    # This runs concurrently — display_pdf returns immediately.
    async def _prefetch() -> None:
        if url in _pdf_cache:
            return
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=120.0), follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            if len(resp.content) <= MAX_PDF_SIZE:
                _pdf_cache[url] = resp.content
                logger.info("display_pdf: pre-cached %d bytes for %s", len(resp.content), url)
        except Exception as e:
            logger.warning("display_pdf: pre-fetch failed for %s: %s", url, e)

    task = asyncio.create_task(_prefetch())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    has_ui = ctx.client_supports_extension(UI_EXTENSION_ID) if ctx else False
    summary_parts = [
        f"Displaying PDF: {display_title}",
        f"view_uuid: {view_id}",
        "",
        "Use the `interact` tool with this view_uuid to navigate, search, annotate, or extract text.",
        "Actions: navigate (page), search (query), highlight_text (query), add_annotations, get_text, fill_form.",
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
    """Stream PDF data in chunks with pagination metadata.

    Uses HTTP Range requests when the origin supports them — only fetches
    the requested chunk, not the entire file. For a 63 MB PDF, each tool
    call transfers only ~4 MB instead of blocking on a full download.
    """
    try:
        chunk, total_bytes = await _read_pdf_range(url, offset, CHUNK_SIZE)
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
# list_pdfs — gallery of available PDFs (app-visible only)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="list_pdfs",
    description="List available PDF documents for the gallery view.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def list_pdfs() -> ToolResult:
    """Return the curated gallery of available PDFs."""
    from ra_mcp_pdf_mcp.gallery import get_gallery_items

    items = get_gallery_items()
    return ToolResult(
        content=[types.TextContent(type="text", text=f"{len(items)} PDFs available")],
        structured_content={"items": items},
    )


# ---------------------------------------------------------------------------
# search_pdf — server-side full-text search (app-visible only)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="search_pdf",
    description="Search for text across all pages of a PDF. Returns per-page match counts. Much faster than client-side search for large PDFs.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def search_pdf(
    url: Annotated[str, Field(description="URL of the PDF file (must be cached from a previous display_pdf call).")],
    term: Annotated[str, Field(description="The search term to find.")],
) -> ToolResult:
    """Search all pages of a cached PDF using pymupdf (server-side, fast)."""
    import fitz  # pymupdf

    if not term or not term.strip():
        return ToolResult(
            content=[types.TextContent(type="text", text="No search term provided.")],
            structured_content={"pageMatches": [], "totalMatches": 0},
        )

    # Get PDF bytes — from cache or fetch fresh
    if url not in _pdf_cache:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=120.0), follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
            if len(resp.content) <= MAX_PDF_SIZE:
                _pdf_cache[url] = resp.content
        except Exception as e:
            return _error_result(f"Failed to fetch PDF for search: {e}")

    if url not in _pdf_cache:
        return _error_result("PDF too large to search server-side.")

    pdf_bytes = _pdf_cache[url]
    search_term = term.strip()

    def _search() -> tuple[list[dict], int]:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_matches: list[dict] = []
        total = 0
        for i in range(len(doc)):
            page = doc[i]
            # text_instances returns list of Rect for each match
            instances = page.search_for(search_term)
            count = len(instances)
            if count > 0:
                page_matches.append({"pageIndex": i, "pageNum": i + 1, "matchCount": count})
                total += count
        doc.close()
        return page_matches, total

    # Run in thread to not block the event loop
    page_matches, total_matches = await asyncio.to_thread(_search)

    pages_with = len(page_matches)
    summary = f"Found {total_matches} match{'es' if total_matches != 1 else ''} across {pages_with} page{'s' if pages_with != 1 else ''}."
    logger.info("search_pdf: term=%r, %s", search_term, summary)

    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content={"pageMatches": page_matches, "totalMatches": total_matches},
    )


# ---------------------------------------------------------------------------
# UI Resource
# ---------------------------------------------------------------------------


# Whitelist PDF source domains so the iframe can fetch() directly (bypasses MCP transport)
_PDF_DOMAINS = [
    "https://huggingface.co",
    "https://arxiv.org",
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


async def _read_pdf_range(url: str, offset: int, length: int) -> tuple[bytes, int]:
    """Read a byte range from a PDF. Returns (chunk_bytes, total_size).

    Uses HTTP Range requests when supported by the server — only fetches the
    requested bytes, not the entire file. Falls back to full GET + cache when
    the server returns 200 (no range support) or 501.
    """
    # Fast path: already have the full file cached
    if url in _pdf_cache:
        data = _pdf_cache[url]
        return data[offset : offset + length], len(data)

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=120.0), follow_redirects=True) as client:
        # Try Range request first
        end_byte = offset + length - 1
        resp = await client.get(url, headers={"Range": f"bytes={offset}-{end_byte}"})

        if resp.status_code == 206:
            # Server supports Range — return just this chunk
            content_range = resp.headers.get("Content-Range", "")
            total = 0
            if "/" in content_range:
                size_str = content_range.rsplit("/", 1)[-1]
                if size_str != "*":
                    total = int(size_str)
            return resp.content, total

        if resp.status_code == 501:
            # Server explicitly doesn't support Range — retry as plain GET
            resp = await client.get(url)
            resp.raise_for_status()

        if resp.status_code == 200:
            # Got full body — cache it and slice
            data = resp.content
            content_length = int(resp.headers.get("Content-Length", len(data)))
            if content_length > MAX_PDF_SIZE:
                msg = f"PDF too large to cache: {content_length} bytes (max {MAX_PDF_SIZE})"
                raise ValueError(msg)
            _pdf_cache[url] = data
            return data[offset : offset + length], len(data)

        resp.raise_for_status()  # raises for any other status
        return b"", 0  # unreachable, but satisfies type checker


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

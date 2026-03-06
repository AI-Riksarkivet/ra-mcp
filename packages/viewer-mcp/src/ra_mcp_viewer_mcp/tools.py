"""
Document Viewer MCP App — Tool & resource registrations.

Tools:
  - view_document: entry point, resolves reference code → URLs, returns transcription for the model
  - load_page: fetches a single page on demand (called by View via callServerTool)
  - load_thumbnails: batch-fetches thumbnail images (called by View via callServerTool)
"""

import asyncio
import logging
from pathlib import Path
from typing import Annotated

from fastmcp import Context
from fastmcp.server.apps import UI_EXTENSION_ID, AppConfig
from fastmcp.tools import ToolResult
from mcp import types
from pydantic import Field

from ra_mcp_browse_lib.browse_operations import BrowseOperations
from ra_mcp_common.http_client import default_http_client
from ra_mcp_viewer_mcp import viewer_mcp as mcp
from ra_mcp_viewer_mcp.fetchers import build_page_data, fetch_and_parse_text_layer, fetch_thumbnail_as_data_url


logger = logging.getLogger("ra_mcp.viewer.tools")

DIST_DIR = Path(__file__).parent / "dist"
RESOURCE_URI = "ui://document-viewer/mcp-app.html"


@mcp.tool(
    name="view_document",
    description=(
        "Display document pages with zoomable images and text layer overlays. "
        "Takes a reference code and page specification (same as browse_document). "
        "Use after search to visually inspect document pages with transcription overlay. "
        "Use highlight_term to pre-populate the search bar and highlight matching text lines."
    ),
    app=AppConfig(resource_uri=RESOURCE_URI),
)
async def view_document(
    reference_code: Annotated[str, Field(description="Document reference code from search results (e.g. 'SE/RA/420422/01').")],
    pages: Annotated[str, Field(description="Page specification: single ('5'), range ('1-10'), or comma-separated ('5,7,9').")],
    ctx: Context,
    highlight_term: Annotated[str | None, Field(description="Optional search term to pre-populate the search bar and highlight matching text lines.")] = None,
    max_pages: Annotated[int, Field(description="Maximum pages to retrieve.", le=20)] = 20,
) -> ToolResult:
    """View document pages with zoomable images and text layer overlays."""
    if not reference_code or not reference_code.strip():
        return ToolResult(content=[types.TextContent(type="text", text="Error: reference_code must not be empty.")])
    if not pages or not pages.strip():
        return ToolResult(content=[types.TextContent(type="text", text="Error: pages must not be empty.")])

    try:
        browse_ops = BrowseOperations(http_client=default_http_client)
        browse_result = await browse_ops.browse_document(
            reference_code=reference_code,
            pages=pages,
            highlight_term=highlight_term,
            max_pages=max_pages,
        )
    except Exception as e:
        logger.error("view_document: failed to resolve document: %s", e)
        return ToolResult(content=[types.TextContent(type="text", text=f"Error resolving document: {e}")])

    if not browse_result.contexts:
        return ToolResult(content=[types.TextContent(type="text", text=f"No pages found for {reference_code} pages={pages}.")])

    image_urls = [page_ctx.image_url for page_ctx in browse_result.contexts]
    text_layer_urls = [page_ctx.alto_url for page_ctx in browse_result.contexts]
    page_numbers = [page_ctx.page_number for page_ctx in browse_result.contexts]

    has_ui = ctx.client_supports_extension(UI_EXTENSION_ID)

    # Build summary with first page transcription
    first_page = browse_result.contexts[0]
    transcription = first_page.full_text.strip() if first_page.full_text else ""

    summary_parts = [f"Displaying {len(browse_result.contexts)} page(s) of {reference_code}."]
    if transcription:
        summary_parts.append(f"Page {first_page.page_number} transcription:")
        summary_parts.append(transcription)
    else:
        summary_parts.append(f"Page {first_page.page_number}: (no transcribed text)")

    if not has_ui:
        summary_parts.append("\nImage URLs:\n" + "\n".join(image_urls))
    summary = "\n".join(summary_parts)

    logger.info("view_document: %s pages=%s, resolved %d page(s)", reference_code, pages, len(browse_result.contexts))
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content={
            "image_urls": image_urls,
            "text_layer_urls": text_layer_urls,
            "page_numbers": page_numbers,
            "highlight_term": highlight_term or "",
            "reference_code": reference_code,
        },
    )


@mcp.tool(
    name="load_page",
    description="Load a single document page (image + text layer). Used by the viewer for pagination.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def load_page(
    image_url: Annotated[str, "Image URL for the page."],
    text_layer_url: Annotated[str, "Text layer XML URL (ALTO/PAGE) for the page."],
    page_index: Annotated[int, "Zero-based page index."],
) -> ToolResult:
    """Fetch a single page on demand."""
    page, errors = await build_page_data(page_index, image_url, text_layer_url)

    total_lines = len(page.get("textLayer", {}).get("textLines", []))
    summary = f"Page {page_index + 1}: {total_lines} text lines."
    if errors:
        summary += f" Errors: {'; '.join(errors)}"

    logger.info(f"load_page: page {page_index + 1} loaded, {total_lines} text lines")
    logger.debug(f"load_page: image_url={image_url}, text_layer_url={text_layer_url}")
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content={"page": page},
    )


@mcp.tool(
    name="load_thumbnails",
    description="Load thumbnail images for a batch of document pages. Used by the viewer for lazy-loading the thumbnail strip.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def load_thumbnails(
    image_urls: Annotated[list[str], "Image URLs for the pages to thumbnail."],
    page_indices: Annotated[list[int], "Zero-based page indices corresponding to image_urls."],
) -> ToolResult:
    """Fetch and resize a batch of page images into thumbnails (concurrent)."""
    thumbnails: list[dict] = []
    errors: list[str] = []
    sem = asyncio.Semaphore(4)

    async def _fetch_one(url: str, idx: int) -> dict | None:
        async with sem:
            try:
                data_url = await fetch_thumbnail_as_data_url(url)
                return {"index": idx, "dataUrl": data_url}
            except Exception as e:
                logger.error(f"Thumbnail failed for page {idx}: {e}")
                return None

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(_fetch_one(url, idx)) for url, idx in zip(image_urls, page_indices, strict=True)]

    for task, idx in zip(tasks, page_indices, strict=True):
        result = task.result()
        if result:
            thumbnails.append(result)
        else:
            errors.append(f"Page {idx + 1}: failed")

    thumbnails.sort(key=lambda t: t["index"])

    summary = f"Generated {len(thumbnails)} thumbnails."
    if errors:
        summary += f" Errors: {'; '.join(errors)}"

    logger.info(f"load_thumbnails: generated {len(thumbnails)} thumbnail(s)")
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content={"thumbnails": thumbnails},
    )


@mcp.tool(
    name="search_all_pages",
    description="Search for a term across all document pages. Returns match counts per page.",
    app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
)
async def search_all_pages(
    text_layer_urls: Annotated[list[str], "List of text layer XML URLs to search across."],
    term: Annotated[str, "The search term to find in page transcriptions."],
) -> ToolResult:
    """Search all pages concurrently and return per-page match counts."""
    if not term or not term.strip():
        return ToolResult(
            content=[types.TextContent(type="text", text="No search term provided.")],
            structured_content={"pageMatches": [], "totalMatches": 0},
        )

    term_lower = term.strip().lower()
    sem = asyncio.Semaphore(6)

    async def _search_page(page_index: int, url: str) -> dict | None:
        if not url or not url.startswith(("http://", "https://")):
            return None
        async with sem:
            try:
                text_layer = await fetch_and_parse_text_layer(url)
            except Exception as e:
                logger.warning("search_all_pages: failed to fetch page %d: %s", page_index, e)
                return None
            count = 0
            for line in text_layer.get("textLines", []):
                transcription = line.get("transcription", "")
                if term_lower in transcription.lower():
                    count += 1
            if count > 0:
                return {"pageIndex": page_index, "matchCount": count}
            return None

    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(_search_page(i, url)) for i, url in enumerate(text_layer_urls)]

    page_matches = [r for t in tasks if (r := t.result()) is not None]
    page_matches.sort(key=lambda m: m["pageIndex"])
    total_matches = sum(m["matchCount"] for m in page_matches)

    pages_with_matches = len(page_matches)
    summary = f"Found {total_matches} match{'es' if total_matches != 1 else ''} across {pages_with_matches} page{'s' if pages_with_matches != 1 else ''}."
    logger.info("search_all_pages: term=%r, %s", term, summary)

    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content={"pageMatches": page_matches, "totalMatches": total_matches},
    )


@mcp.resource(uri=RESOURCE_URI)
def get_ui_resource() -> str:
    html_path = DIST_DIR / "mcp-app.html"
    if not html_path.exists():
        raise FileNotFoundError(f"UI resource not found: {html_path}")
    return html_path.read_text(encoding="utf-8")

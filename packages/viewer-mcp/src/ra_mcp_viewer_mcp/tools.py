"""
Document Viewer MCP App — Tool & resource registrations.

Tools:
  - view_document: entry point, returns transcription for the model
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

from ra_mcp_viewer_mcp import viewer_mcp as mcp
from ra_mcp_viewer_mcp.fetchers import build_page_data, fetch_and_parse_text_layer, fetch_thumbnail_as_data_url


logger = logging.getLogger("ra_mcp.viewer.tools")

DIST_DIR = Path(__file__).parent / "dist"
RESOURCE_URI = "ui://document-viewer/mcp-app.html"


@mcp.tool(
    name="view_document",
    description=(
        "Display document pages with zoomable images and text layer overlays. "
        "Provide paired lists: image_urls[i] pairs with text_layer_urls[i]. "
        "Empty text_layer_urls entries are allowed for pages without transcription. "
        "Optionally include per-page metadata for display in the viewer. "
        "Use highlight_term to pre-populate the search bar and highlight matching text lines."
    ),
    app=AppConfig(resource_uri=RESOURCE_URI),
)
async def view_document(
    image_urls: Annotated[list[str], "List of image URLs (one per page)."],
    text_layer_urls: Annotated[list[str], "List of text layer XML URLs (ALTO/PAGE) paired with image_urls. Use empty string for pages without transcription."],
    ctx: Context,
    metadata: Annotated[list[str] | None, "Per-page metadata descriptions, paired with image_urls."] = None,
    highlight_term: Annotated[str | None, "Optional search term to pre-populate the search bar and highlight matching text lines."] = None,
    highlight_term_color: Annotated[str | None, "Optional hex color for search highlights (default: amber #f59e0b)."] = None,
) -> ToolResult:
    """View document pages with zoomable images and text layer overlays."""
    if len(image_urls) != len(text_layer_urls):
        return ToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=f"Error: mismatched URL counts ({len(image_urls)} images vs {len(text_layer_urls)} text layer files)",
                )
            ],
        )

    has_ui = ctx.client_supports_extension(UI_EXTENSION_ID)

    transcription = ""
    first_url = text_layer_urls[0]
    if first_url and first_url.startswith(("http://", "https://")):
        first_text_layer = await fetch_and_parse_text_layer(first_url)
        text_lines = first_text_layer.get("textLines", [])
        transcription = "\n".join(line["transcription"] for line in text_lines)

    summary_parts = [f"Displaying {len(image_urls)}-page document. Page 1 transcription:"]
    if transcription:
        summary_parts.append(transcription)
    else:
        summary_parts.append("(no transcribed text on this page)")

    if not has_ui:
        summary_parts.append("\nImage URLs:\n" + "\n".join(image_urls))
    summary = "\n".join(summary_parts)

    logger.info(f"view_document: displaying {len(image_urls)} page(s) with {len(text_layer_urls)} text layer(s)")
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
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

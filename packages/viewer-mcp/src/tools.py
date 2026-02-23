"""
Document Viewer MCP App — Tool & resource registrations.

Tools:
  - view-document: entry point, returns transcription for the model
  - load-page: fetches a single page on demand (called by View via callServerTool)
  - load-thumbnails: batch-fetches thumbnail images (called by View via callServerTool)
"""

import asyncio
import logging
from pathlib import Path
from typing import Annotated

from fastmcp import Context
from fastmcp.server.apps import AppConfig, UI_EXTENSION_ID
from fastmcp.tools import ToolResult
from mcp import types

from src import mcp
from src.fetchers import build_page_data, fetch_and_parse_text_layer, fetch_thumbnail_as_data_url

logger = logging.getLogger(__name__)

DIST_DIR = Path(__file__).parent.parent / "dist"
RESOURCE_URI = "ui://document-viewer/mcp-app.html"

@mcp.tool(
    name="view-document",
    description=(
        "Display document pages with zoomable images and text layer overlays. "
        "Provide paired lists: image_urls[i] pairs with text_layer_urls[i]. "
        "Empty text_layer_urls entries are allowed for pages without transcription. "
        "Optionally include per-page metadata for display in the viewer."
    ),
    app=AppConfig(resource_uri=RESOURCE_URI),
)
async def view_document(
    image_urls: Annotated[list[str], "List of image URLs (one per page)."],
    text_layer_urls: Annotated[list[str], "List of text layer XML URLs (ALTO/PAGE) paired with image_urls. Use empty string for pages without transcription."],
    ctx: Context,
    metadata: Annotated[list[str] | None, "Per-page metadata descriptions, paired with image_urls."] = None,
) -> ToolResult:
    """View document pages with zoomable images and text layer overlays."""
    if len(image_urls) != len(text_layer_urls):
        return ToolResult(
            content=[types.TextContent(
                type="text",
                text=f"Error: mismatched URL counts ({len(image_urls)} images vs {len(text_layer_urls)} text layer files)",
            )],
        )

    has_ui = ctx.client_supports_extension(UI_EXTENSION_ID)

    transcription = ""
    if text_layer_urls[0]:
        first_text_layer = await fetch_and_parse_text_layer(text_layer_urls[0])
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

    logger.info(f"view-document: {len(image_urls)} pages, {len(text_layer_urls)} text layers")
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
    )


@mcp.tool(
    name="load-page",
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

    logger.info(f"load-page: {summary}")
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content={"page": page},
    )


@mcp.tool(
    name="load-thumbnails",
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
        tasks = [
            tg.create_task(_fetch_one(url, idx))
            for url, idx in zip(image_urls, page_indices)
        ]

    for task, idx in zip(tasks, page_indices):
        result = task.result()
        if result:
            thumbnails.append(result)
        else:
            errors.append(f"Page {idx + 1}: failed")

    thumbnails.sort(key=lambda t: t["index"])

    summary = f"Generated {len(thumbnails)} thumbnails."
    if errors:
        summary += f" Errors: {'; '.join(errors)}"

    logger.info(f"load-thumbnails: {summary}")
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content={"thumbnails": thumbnails},
    )


@mcp.resource(uri=RESOURCE_URI)
def get_ui_resource() -> str:
    html_path = DIST_DIR / "mcp-app.html"
    if not html_path.exists():
        raise FileNotFoundError(f"UI resource not found: {html_path}")
    return html_path.read_text(encoding="utf-8")

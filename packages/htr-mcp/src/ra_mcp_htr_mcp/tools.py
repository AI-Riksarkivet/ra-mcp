"""
Riksarkivet HTR MCP Server.

This module sets up the FastMCP server and registers the htr_transcribe tool,
which delegates to a remote Gradio Space via gradio_client.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp import FastMCP
from gradio_client import Client


logger = logging.getLogger(__name__)

HTR_SPACE_URL = os.getenv("HTR_SPACE_URL", "https://riksarkivet-htr-demo.hf.space")

_client: Client | None = None


def _get_client() -> Client:
    """Return a lazily-initialized Gradio client for the HTR Space."""
    global _client
    if _client is None:
        logger.info("Connecting to HTR Space: %s", HTR_SPACE_URL)
        _client = Client(HTR_SPACE_URL)
    return _client


htr_mcp = FastMCP(
    name="ra-htr-mcp",
    instructions="""
    🖊️ Riksarkivet HTR MCP Server

    This server provides handwritten text recognition (HTR) for historical documents
    via a remote Gradio Space running HTRflow.

    AVAILABLE TOOL:

    📝 htr_transcribe - Transcribe handwritten document images
       - Accepts image URLs (http/https)
       - Supports Swedish, Norwegian, English, and medieval documents
       - Returns viewer URL, per-page JSON, and archival export (ALTO XML, PAGE XML, or JSON)

    WORKFLOW:
    1. Collect image URLs for the document pages to transcribe
    2. Call htr_transcribe with the image URLs
    3. Use the returned viewer_url for interactive viewing with polygon overlays
    4. Use pages_url for structured per-page transcription data
    5. Use export_url for archival export files
    """,
)


@htr_mcp.tool()
async def htr_transcribe(
    image_urls: list[str],
    language: str = "swedish",
    layout: str = "single_page",
    export_format: str = "alto_xml",
    custom_yaml: str | None = None,
) -> dict[str, Any]:
    """Transcribe handwritten documents and return results as file URLs.

    Returns: dict with file URLs:
        viewer_url: Interactive gallery viewer with polygon overlays,
            search, confidence scores, and text download.
        pages_url: JSON with per-page transcription lines
            (id, text, confidence per line).
        export_url: Archival export file in the requested format.
        export_format: The requested format (echoed back).

    Args:
        image_urls: List of full server URLs to process (from upload endpoint
                    or direct http/https URLs).
        language: Document language: "swedish" (default), "norwegian",
                  "english", or "medieval".
        layout: Page layout: "single_page" (default) or "spread" (two-page opening).
        export_format: Export format: "alto_xml" (default), "page_xml", or "json".
        custom_yaml: Optional HTRflow YAML pipeline config string. Overrides
                     language/layout when provided.
    """
    client = _get_client()
    result = client.predict(
        image_urls=image_urls,
        language=language,
        layout=layout,
        export_format=export_format,
        custom_yaml=custom_yaml,
        api_name="/htr_transcribe",
    )
    return result

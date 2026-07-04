"""
Riksarkivet HTR MCP Server.

This module sets up the FastMCP server and registers the htr_transcribe tool,
which delegates to a remote Gradio Space via gradio_client.
"""

from __future__ import annotations

import logging
import os
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from gradio_client import Client
from pydantic import BaseModel, Field


logger = logging.getLogger("ra_mcp.htr.tools")

HTR_SPACE_URL = os.getenv("HTR_SPACE_URL", "https://riksarkivet-htr-demo.hf.space")
HTR_TIMEOUT = float(os.getenv("HTR_TIMEOUT", "300"))

_client: Client | None = None


def _get_client() -> Client:
    """Return a lazily-initialized Gradio client for the HTR Space."""
    global _client
    if _client is None:
        logger.info("Connecting to HTR Space: %s", HTR_SPACE_URL)
        _client = Client(HTR_SPACE_URL)
    return _client


class HtrResult(BaseModel):
    """Result from an HTR transcription job."""

    viewer_url: str = Field(description="Interactive gallery viewer with polygon overlays, search, confidence scores, and text download")
    pages_url: str = Field(description="JSON with per-page transcription lines (id, text, confidence per line)")
    export_url: str = Field(description="Archival export file in the requested format")
    export_format: str = Field(description="The export format that was used (echoed back)")


htr_mcp = FastMCP(
    name="ra-htr-mcp",
    instructions="""
    Riksarkivet HTR MCP Server

    Provides handwritten text recognition (HTR) for historical documents
    via a remote Gradio Space running HTRflow.

    AVAILABLE TOOL:

    htr_transcribe - Transcribe handwritten document images
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


@htr_mcp.tool(
    annotations={
        "title": "Transcribe Handwritten Documents",
        "readOnlyHint": True,
        "openWorldHint": True,
        "idempotentHint": True,
    },
    timeout=HTR_TIMEOUT,
)
async def htr_transcribe(
    image_urls: Annotated[list[str], Field(description="Image URLs to process (http/https URLs)")],
    language: Annotated[
        Literal["swedish", "norwegian", "english", "medieval"],
        Field(description="Document language"),
    ] = "swedish",
    layout: Annotated[
        Literal["single_page", "spread"],
        Field(description="Page layout: single_page or spread (two-page opening)"),
    ] = "single_page",
    export_format: Annotated[
        Literal["alto_xml", "page_xml", "json"],
        Field(description="Archival export format"),
    ] = "alto_xml",
    custom_yaml: Annotated[
        str | None,
        Field(description="Optional HTRflow YAML pipeline config. Overrides language/layout when provided"),
    ] = None,
) -> HtrResult:
    """Transcribe handwritten documents and return results as file URLs.

    Sends images to the HTRflow Gradio Space for AI-powered handwritten text
    recognition. Returns URLs to an interactive viewer, per-page JSON
    transcriptions, and an archival export file.
    """
    try:
        client = _get_client()
    except Exception as e:
        raise ToolError(f"Failed to connect to HTR Space at {HTR_SPACE_URL}: {e}") from e

    try:
        result = client.predict(
            image_urls=image_urls,
            language=language,
            layout=layout,
            export_format=export_format,
            custom_yaml=custom_yaml,
            api_name="/htr_transcribe",
        )
    except Exception as e:
        raise ToolError(f"HTR transcription failed: {e}") from e

    return HtrResult(**result)

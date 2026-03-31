"""Data models for the PDF Viewer MCP App."""

from __future__ import annotations

from pydantic import BaseModel


class PdfViewerState(BaseModel):
    """Per-view session state for a PDF viewer instance.

    The UI polls get_pdf_state with its view_id to detect LLM-initiated
    changes (search_term, go_to_page). State auto-expires after TTL.
    """

    view_id: str = ""
    version: int = 0

    # PDF source
    url: str = ""
    title: str = "Document"
    source_url: str = ""

    # Navigation
    current_page: int = 1
    total_pages: int = 0
    go_to_page: int = -1  # -1 = no nav request, 0+ = jump to this page (0-based)

    # Search
    search_term: str = ""

    # Display
    request_fullscreen: bool = False

"""Data models for the PDF Viewer MCP App."""

from __future__ import annotations

from pydantic import BaseModel


class PdfViewerState(BaseModel):
    """Per-view session state for a PDF viewer instance.

    The UI polls get_pdf_state with its view_id to detect LLM-initiated
    changes (navigate, search, annotate). State auto-expires after TTL.
    """

    view_id: str = ""
    version: int = 0

    # PDF source
    url: str = ""
    title: str = "Document"
    source_url: str = ""  # original URL (e.g. arxiv page)

    # Navigation
    current_page: int = 1
    total_pages: int = 0

    # Display
    request_fullscreen: bool = False
    is_local: bool = False  # whether the PDF is a local file (proxied)


class PdfCommand(BaseModel):
    """A command from the server to the viewer, queued via interact tool."""

    type: str
    # Navigation
    page: int | None = None
    # Search
    query: str | None = None
    match_index: int | None = None
    # Zoom
    scale: float | None = None
    # Annotations
    annotations: list[dict] | None = None  # type: ignore[type-arg]
    ids: list[str] | None = None
    # Text extraction
    request_id: str | None = None
    intervals: list[dict] | None = None  # type: ignore[type-arg]
    get_text: bool = False
    get_screenshots: bool = False
    # highlight_text
    id: str | None = None
    color: str | None = None
    content: str | None = None
    # Form fill
    fields: list[dict] | None = None  # type: ignore[type-arg]


class InteractResult(BaseModel):
    """Result returned by the interact tool to the LLM."""

    message: str
    is_error: bool = False

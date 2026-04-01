from typing import NamedTuple

from pydantic import BaseModel

from ra_mcp_xml.models import TextLayer, TextLine  # Single source of truth


# Re-export for convenience
__all__ = ["ResolvedDocument", "TextLayer", "TextLine", "ViewerState"]


class ResolvedDocument(NamedTuple):
    """Result of resolving a reference code to page URLs."""

    image_urls: list[str]
    text_layer_urls: list[str]
    page_numbers: list[int]
    bildvisning_urls: list[str]
    document_info: str  # markdown-formatted metadata


class ViewerState(BaseModel):
    """Per-view state keyed by view_id. Polled by the View iframe via get_viewer_state."""

    view_id: str = ""
    version: int = 0
    image_urls: list[str] = []
    text_layer_urls: list[str] = []
    page_numbers: list[int] = []
    highlight_term: str = ""
    reference_code: str = ""
    bildvisning_urls: list[str] = []
    document_info: str = ""  # markdown-formatted document metadata
    go_to_page: int = -1  # -1 = no navigation request, 0+ = jump to this page index
    request_fullscreen: bool = False

from typing import NamedTuple

from pydantic import BaseModel


class ResolvedDocument(NamedTuple):
    """Result of resolving a reference code to page URLs."""

    image_urls: list[str]
    text_layer_urls: list[str]
    page_numbers: list[int]


class TextLine(BaseModel):
    id: str
    polygon: str
    transcription: str
    hpos: int
    vpos: int
    width: int
    height: int
    confidence: float | None = None


class TextLayer(BaseModel):
    text_lines: list[TextLine]
    page_width: int
    page_height: int
    full_text: str


class ViewerState(BaseModel):
    """Per-view state keyed by view_id. Polled by the View iframe via get_viewer_state."""

    view_id: str = ""
    version: int = 0
    image_urls: list[str] = []
    text_layer_urls: list[str] = []
    page_numbers: list[int] = []
    highlight_term: str = ""
    reference_code: str = ""
    go_to_page: int = -1  # -1 = no navigation request, 0+ = jump to this page index
    request_fullscreen: bool = False

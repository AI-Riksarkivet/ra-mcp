from pydantic import BaseModel


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

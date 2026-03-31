"""Data models for the PDF Viewer MCP App."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PdfViewerState(BaseModel):
    """Per-view session state for a PDF viewer instance."""

    view_id: str = ""
    version: int = 0
    url: str = ""
    title: str = "Document"
    source_url: str = ""
    current_page: int = 1
    total_pages: int = 0
    go_to_page: int = -1
    search_term: str = ""
    request_fullscreen: bool = False


class MatchedBlock(BaseModel):
    """A text block that matched a search term, with exact bounding box."""

    model_config = ConfigDict(populate_by_name=True)

    text: str
    bbox: list[int]
    block_type: str
    match_count: int

    def to_structured(self) -> dict:
        return {
            "text": self.text,
            "bbox": self.bbox,
            "blockType": self.block_type,
            "matchCount": self.match_count,
        }


class PageMatch(BaseModel):
    """Search results for a single page."""

    page_index: int
    page_num: int
    match_count: int
    page_bbox: list[int]
    blocks: list[MatchedBlock]

    def to_structured(self) -> dict:
        return {
            "pageIndex": self.page_index,
            "pageNum": self.page_num,
            "matchCount": self.match_count,
            "pageBbox": self.page_bbox,
            "blocks": [b.to_structured() for b in self.blocks],
        }


class SearchResult(BaseModel):
    """Full search result across all pages."""

    page_matches: list[PageMatch]
    total_matches: int

    def to_structured(self) -> dict:
        return {
            "pageMatches": [pm.to_structured() for pm in self.page_matches],
            "totalMatches": self.total_matches,
        }

    def summary(self, term: str) -> str:
        """Human-readable summary with text snippets for model context."""
        pages_with = len(self.page_matches)
        lines = [
            f"Found {self.total_matches} match{'es' if self.total_matches != 1 else ''} for '{term}' across {pages_with} page{'s' if pages_with != 1 else ''}.",
        ]
        snippet_count = 0
        for pm in self.page_matches:
            for block in pm.blocks:
                if snippet_count >= 10:
                    break
                lines.append(f"  p.{pm.page_num}: {block.text[:200]}")
                snippet_count += 1
            if snippet_count >= 10:
                break
        return "\n".join(lines)

"""Block-level full-text search across structured PDF pages."""

from __future__ import annotations

import logging
import re

from ra_mcp_pdf_mcp.models import MatchedBlock, PageMatch, SearchResult


logger = logging.getLogger("ra_mcp.pdf.search")

_STRIP_HTML = re.compile(r"<[^>]+>")


def html_to_text(html: str) -> str:
    """Strip HTML tags, returning plain text."""
    return _STRIP_HTML.sub(" ", html).strip()


def search_pages(pages: list[dict], term: str) -> SearchResult:
    """Search structured JSON pages for a term. Returns results with exact bbox per block."""
    term_lower = term.lower()
    page_matches: list[PageMatch] = []
    total = 0

    for page_data in pages:
        page_idx: int = page_data["page"]
        page_bbox: list[int] = page_data.get("bbox", [0, 0, 0, 0])
        matched_blocks: list[MatchedBlock] = []
        page_count = 0

        for block in page_data.get("children", []):
            html: str = block.get("html", "")
            if not html:
                continue
            text = html_to_text(html)

            count = _count_occurrences(text.lower(), term_lower)
            if count > 0:
                page_count += count
                matched_blocks.append(
                    MatchedBlock(
                        text=text[:300],
                        bbox=block["bbox"],
                        block_type=block.get("block_type", ""),
                        match_count=count,
                    )
                )

        if page_count > 0:
            page_matches.append(
                PageMatch(
                    page_index=page_idx,
                    page_num=page_idx + 1,
                    match_count=page_count,
                    page_bbox=page_bbox,
                    blocks=matched_blocks,
                )
            )
            total += page_count

    result = SearchResult(page_matches=page_matches, total_matches=total)
    logger.info("search: term=%r, %d matches across %d pages", term, total, len(page_matches))
    return result


def _count_occurrences(text: str, term: str) -> int:
    count = 0
    start = 0
    while True:
        idx = text.find(term, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(term)
    return count

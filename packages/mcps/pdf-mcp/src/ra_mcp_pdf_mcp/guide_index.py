"""LanceDB-backed full-text search over the PDF guides (Swedish FTS).

Replaces the previous Python substring scan with a BM25 + Swedish-stemming index
built from the guides' structured blocks — so ``kung`` matches ``kungar`` /
``kungens`` and results rank by relevance instead of raw occurrence order. Each
block is one row that keeps its bbox, so the viewer can still highlight matches
precisely; the block hits are regrouped back into the per-page ``SearchResult``
the app already consumes.

The index lives in a process-lifetime in-memory LanceDB (the guides are 3 small
static documents), rebuilt only when the set of cached guides changes.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import build_fts_index, equals, get_lancedb, lancedb_fts_search
from ra_mcp_pdf_mcp.models import MatchedBlock, PageMatch, SearchResult
from ra_mcp_pdf_mcp.search import _count_occurrences, html_to_text


if TYPE_CHECKING:
    from ra_mcp_pdf_mcp.cache import LRUCache

_GUIDE_DB_URI = "memory://ra-mcp-pdf-guides"
_TABLE = "guides"
# Bound the ranked set we regroup into page matches — far above any real guide's
# match count, and matches the spine's fetch cap semantics.
_MAX_HITS = 2000

_lock = threading.Lock()
_indexed: frozenset[str] | None = None


def _rows(blocks_by_url: dict[str, list[dict]]) -> list[dict]:
    """One row per non-empty text block, carrying its bbox for highlighting."""
    rows: list[dict] = []
    for url, pages in blocks_by_url.items():
        for page in pages:
            page_index = page["page"]
            page_bbox = page.get("bbox", [0, 0, 0, 0])
            for block in page.get("children", []):
                text = html_to_text(block.get("html", ""))
                if not text:
                    continue
                rows.append(
                    {
                        "guide_url": url,
                        "page_index": page_index,
                        "page_bbox": page_bbox,
                        "block_bbox": block["bbox"],
                        "block_type": block.get("block_type", ""),
                        "text": text,
                        "searchable_text": text,
                    }
                )
    return rows


def ensure_guide_index(blocks_cache: LRUCache[list]) -> bool:
    """Build/refresh the Swedish-FTS guide index from the cached guide blocks.

    Rebuilds only when the set of cached guide URLs changes (the 3 guides are
    static, so after preload this is a no-op). Returns True if the index is
    searchable, False if no guide blocks are cached yet.
    """
    global _indexed
    blocks_by_url = dict(blocks_cache.items())
    signature = frozenset(blocks_by_url)
    if not blocks_by_url:
        return False
    if _indexed is not None and signature == _indexed:
        return True
    with _lock:
        if _indexed is not None and signature == _indexed:
            return True
        rows = _rows(blocks_by_url)
        if not rows:
            return False
        db = get_lancedb(_GUIDE_DB_URI)
        db.create_table(_TABLE, data=rows, mode="overwrite")
        build_fts_index(db, _TABLE, column="searchable_text")
        _indexed = signature
        return True


def _regroup_by_page(records: list[dict], term_lower: str) -> SearchResult:
    """Regroup FTS block hits into per-page matches in document order."""
    by_page: dict[int, PageMatch] = {}
    total = 0
    for rec in records:
        text = rec["text"]
        # A stem-only match (e.g. "häst" query hitting a "hästar" block) has no
        # literal occurrence, but FTS confirmed the hit — floor the count at 1.
        count = _count_occurrences(text.lower(), term_lower) or 1
        total += count
        page_index = int(rec["page_index"])
        pm = by_page.get(page_index)
        if pm is None:
            pm = PageMatch(
                page_index=page_index,
                page_num=page_index + 1,
                match_count=0,
                page_bbox=[int(v) for v in rec["page_bbox"]],
                blocks=[],
            )
            by_page[page_index] = pm
        pm.blocks.append(
            MatchedBlock(
                text=text[:300],
                bbox=[int(v) for v in rec["block_bbox"]],
                block_type=rec.get("block_type", ""),
                match_count=count,
            )
        )
        pm.match_count += count

    page_matches = [by_page[k] for k in sorted(by_page)]
    return SearchResult(page_matches=page_matches, total_matches=total)


def search_guide_index(term: str, *, guide_url: str | None = None) -> SearchResult:
    """Full-text search the guide index, regrouped into the per-page SearchResult.

    ``guide_url`` restricts to a single guide (search_pdf); omit it to search all
    guides. Matches use Swedish stemming + BM25 ranking; blocks are regrouped by page
    in document order so the viewer highlights them in place.
    """
    db = get_lancedb(_GUIDE_DB_URI)
    where = equals("guide_url", guide_url) if guide_url else None
    result = lancedb_fts_search(db, _TABLE, term, limit=_MAX_HITS, where=where)
    return _regroup_by_page(result.records, term.lower())


def search_guides_grouped(term: str) -> dict[str, SearchResult]:
    """Search ALL guides in ONE FTS query, regrouped per guide_url then per page.

    Used by the search_guides tool, which previously ran a separate query per guide
    (N+1). One query over the shared table returns every guide's hits; we bucket the
    records by their guide_url field and regroup each bucket by page.
    """
    db = get_lancedb(_GUIDE_DB_URI)
    result = lancedb_fts_search(db, _TABLE, term, limit=_MAX_HITS, where=None)
    term_lower = term.lower()
    by_guide: dict[str, list[dict]] = {}
    for rec in result.records:
        by_guide.setdefault(rec["guide_url"], []).append(rec)
    return {url: _regroup_by_page(recs, term_lower) for url, recs in by_guide.items()}

"""Full-text search operations over the Filmcensur LanceDB table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import FILMREG_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a Filmcensur search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class FilmcensurSearch:
    """Search operations over the Filmcensur LanceDB table."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_filmreg(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        filmkategori: str | None = None,
        produktionsland: str | None = None,
        aaldersgraens: str | None = None,
    ) -> SearchResult:
        """Search the Filmreg table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            filmkategori: Optional case-insensitive substring filter on filmkategori.
            produktionsland: Optional case-insensitive substring filter on produktionsland.
            aaldersgraens: Optional case-insensitive substring filter on aaldersgraens.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([filmkategori, produktionsland, aaldersgraens])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(FILMREG_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        # Apply post-filters
        if filmkategori:
            filmkategori_lower = filmkategori.lower()
            rows = [r for r in rows if filmkategori_lower in r.get("filmkategori", "").lower()]
        if produktionsland:
            produktionsland_lower = produktionsland.lower()
            rows = [r for r in rows if produktionsland_lower in r.get("produktionsland", "").lower()]
        if aaldersgraens:
            aaldersgraens_lower = aaldersgraens.lower()
            rows = [r for r in rows if aaldersgraens_lower in r.get("aaldersgraens", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

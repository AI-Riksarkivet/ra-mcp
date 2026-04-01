"""Full-text search operations over the Suffrage LanceDB tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import FKPR_TABLE, ROSTRATT_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a suffrage search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class SuffrageSearch:
    """Search operations over the Suffrage LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_rostratt(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        lan: str | None = None,
        ortens_namn: str | None = None,
    ) -> SearchResult:
        """Search the Rösträtt table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            lan: Optional case-insensitive substring filter on county (län).
            ortens_namn: Optional case-insensitive substring filter on town name.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([lan, ortens_namn])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(ROSTRATT_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        # Apply post-filters
        if lan:
            lan_lower = lan.lower()
            rows = [r for r in rows if lan_lower in r.get("lan", "").lower()]
        if ortens_namn:
            ortens_lower = ortens_namn.lower()
            rows = [r for r in rows if ortens_lower in r.get("ortens_namn", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

    def search_fkpr(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> SearchResult:
        """Search the FKPR table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        table = self._db.open_table(FKPR_TABLE)
        rows = table.search(keyword, query_type="fts").limit(limit + offset).to_list()

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

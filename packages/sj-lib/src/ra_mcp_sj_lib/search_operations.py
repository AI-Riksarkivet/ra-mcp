"""Full-text search operations over the SJ railway records LanceDB tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import FIRA_TABLE, JUDA_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from an SJ railway records search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class SJSearch:
    """Search operations over the SJ railway records LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_juda(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        fbagrkod2: str | None = None,
    ) -> SearchResult:
        """Search the JUDA property register using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            fbagrkod2: Optional case-insensitive substring filter on owner code.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = bool(fbagrkod2)
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(JUDA_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if fbagrkod2:
            fbagrkod2_lower = fbagrkod2.lower()
            rows = [r for r in rows if fbagrkod2_lower in r.get("fbagrkod2", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

    def search_ritningar(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        dkod: str | None = None,
    ) -> SearchResult:
        """Search the FIRA/SIRA drawings table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            dkod: Optional case-insensitive substring filter on district code.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = bool(dkod)
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(FIRA_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if dkod:
            dkod_lower = dkod.lower()
            rows = [r for r in rows if dkod_lower in r.get("dkod", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

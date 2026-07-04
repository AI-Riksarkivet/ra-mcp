"""Full-text search operations over the SJ railway records LanceDB tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import FIRA_TABLE, JUDA_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["SJSearch", "SearchResult"]


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
        where = combine(
            text_contains("fbagrkod2", fbagrkod2) if fbagrkod2 else None,
        )
        return lancedb_fts_search(self._db, JUDA_TABLE, keyword, limit=limit, offset=offset, where=where)

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
        where = combine(
            text_contains("dkod", dkod) if dkod else None,
        )
        return lancedb_fts_search(self._db, FIRA_TABLE, keyword, limit=limit, offset=offset, where=where)

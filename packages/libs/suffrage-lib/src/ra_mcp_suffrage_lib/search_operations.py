"""Full-text search operations over the Suffrage LanceDB tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import FKPR_TABLE, ROSTRATT_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["SearchResult", "SuffrageSearch"]


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
        where = combine(
            text_contains("lan", lan) if lan else None,
            text_contains("ortens_namn", ortens_namn) if ortens_namn else None,
        )
        return lancedb_fts_search(self._db, ROSTRATT_TABLE, keyword, limit=limit, offset=offset, where=where)

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
        return lancedb_fts_search(self._db, FKPR_TABLE, keyword, limit=limit, offset=offset)

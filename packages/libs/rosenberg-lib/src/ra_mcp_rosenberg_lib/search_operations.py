"""Full-text search operations over the Rosenberg LanceDB table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import ROSENBERG_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["RosenbergSearch", "SearchResult"]


class RosenbergSearch:
    """Search operations over the Rosenberg LanceDB table."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        lan: str | None = None,
        forsamling: str | None = None,
    ) -> SearchResult:
        """Search the Rosenberg table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            lan: Optional case-insensitive substring filter on county (län).
            forsamling: Optional case-insensitive substring filter on parish (församling).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("lan", lan) if lan else None,
            text_contains("forsamling", forsamling) if forsamling else None,
        )
        return lancedb_fts_search(self._db, ROSENBERG_TABLE, keyword, limit=limit, offset=offset, where=where)

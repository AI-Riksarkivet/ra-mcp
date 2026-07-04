"""Full-text search operations over the Wincars LanceDB table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import WINCARS_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["SearchResult", "WincarsSearch"]


class WincarsSearch:
    """Search operations over the Wincars LanceDB table (vehicle registrations)."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        typ: str | None = None,
        hemvist: str | None = None,
        fabrikat: str | None = None,
    ) -> SearchResult:
        """Search the Wincars table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            typ: Optional case-insensitive substring filter on vehicle type (PB, MC, LB, etc.).
            hemvist: Optional case-insensitive substring filter on domicile/location.
            fabrikat: Optional case-insensitive substring filter on make/manufacturer.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("typ", typ) if typ else None,
            text_contains("hemvist", hemvist) if hemvist else None,
            text_contains("fabrikat", fabrikat) if fabrikat else None,
        )
        return lancedb_fts_search(self._db, WINCARS_TABLE, keyword, limit=limit, offset=offset, where=where)

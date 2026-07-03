"""Full-text search operations over the Fältjägare LanceDB table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import FALTJAGARE_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["FaltjagareSearch", "SearchResult"]


class FaltjagareSearch:
    """Search operations over the Fältjägare LanceDB table."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        kompani: str | None = None,
        region: str | None = None,
        befattning: str | None = None,
    ) -> SearchResult:
        """Search the Fältjägare table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            kompani: Optional case-insensitive substring filter on kompani (company).
            region: Optional case-insensitive substring filter on region.
            befattning: Optional case-insensitive substring filter on befattning (rank).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("kompani", kompani) if kompani else None,
            text_contains("region", region) if region else None,
            text_contains("befattning", befattning) if befattning else None,
        )
        return lancedb_fts_search(self._db, FALTJAGARE_TABLE, keyword, limit=limit, offset=offset, where=where)

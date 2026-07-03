"""Full-text search operations over the Sjömanshus LanceDB tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import LIGGARE_TABLE, MATRIKEL_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["SearchResult", "SjomanshusSearch"]


class SjomanshusSearch:
    """Search operations over the Sjömanshus LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_liggare(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        befattning: str | None = None,
        fartyg: str | None = None,
        sjoemanshus: str | None = None,
        hemmahamn: str | None = None,
        kapten: str | None = None,
        redare: str | None = None,
        destination: str | None = None,
    ) -> SearchResult:
        """Search the Liggare table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            befattning: Optional case-insensitive substring filter on befattning_yrke.
            fartyg: Optional case-insensitive substring filter on fartyg.
            sjoemanshus: Optional case-insensitive substring filter on sjoemanshus.
            hemmahamn: Optional case-insensitive substring filter on hemmahamn.
            kapten: Optional case-insensitive substring filter on kapten.
            redare: Optional case-insensitive substring filter on redare.
            destination: Optional case-insensitive substring filter on destination.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("befattning_yrke", befattning) if befattning else None,
            text_contains("fartyg", fartyg) if fartyg else None,
            text_contains("sjoemanshus", sjoemanshus) if sjoemanshus else None,
            text_contains("hemmahamn", hemmahamn) if hemmahamn else None,
            text_contains("kapten", kapten) if kapten else None,
            text_contains("redare", redare) if redare else None,
            text_contains("destination", destination) if destination else None,
        )
        return lancedb_fts_search(self._db, LIGGARE_TABLE, keyword, limit=limit, offset=offset, where=where)

    def search_matrikel(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        sjoemanshus: str | None = None,
    ) -> SearchResult:
        """Search the Matrikel table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            sjoemanshus: Optional case-insensitive substring filter on sjoemanshus.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("sjoemanshus", sjoemanshus) if sjoemanshus else None,
        )
        return lancedb_fts_search(self._db, MATRIKEL_TABLE, keyword, limit=limit, offset=offset, where=where)

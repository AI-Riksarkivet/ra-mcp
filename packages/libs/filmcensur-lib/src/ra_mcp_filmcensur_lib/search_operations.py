"""Full-text search operations over the Filmcensur LanceDB table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import FILMREG_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["FilmcensurSearch", "SearchResult"]


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
        where = combine(
            text_contains("filmkategori", filmkategori) if filmkategori else None,
            text_contains("produktionsland", produktionsland) if produktionsland else None,
            text_contains("aaldersgraens", aaldersgraens) if aaldersgraens else None,
        )
        return lancedb_fts_search(self._db, FILMREG_TABLE, keyword, limit=limit, offset=offset, where=where)

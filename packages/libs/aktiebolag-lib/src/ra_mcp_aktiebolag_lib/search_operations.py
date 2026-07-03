"""Full-text search operations over the Aktiebolag LanceDB tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import BOLAG_TABLE, STYRELSE_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["AktiebolagSearch", "SearchResult"]


class AktiebolagSearch:
    """Search operations over the Aktiebolag LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_bolag(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        styrelsesate: str | None = None,
    ) -> SearchResult:
        """Search the bolag (companies) table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            styrelsesate: Optional case-insensitive substring filter on board seat city.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("styrelsesate", styrelsesate) if styrelsesate else None,
        )
        return lancedb_fts_search(self._db, BOLAG_TABLE, keyword, limit=limit, offset=offset, where=where)

    def search_styrelse(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        titel: str | None = None,
    ) -> SearchResult:
        """Search the styrelse (board members) table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            titel: Optional case-insensitive substring filter on title.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("titel", titel) if titel else None,
        )
        return lancedb_fts_search(self._db, STYRELSE_TABLE, keyword, limit=limit, offset=offset, where=where)

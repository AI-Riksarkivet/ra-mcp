"""Full-text search operations over the court records LanceDB tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, at_least, at_most, combine, lancedb_fts_search, text_contains

from .config import DOMBOKSREGISTER_TABLE, MEDELSTAD_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["CourtSearch", "SearchResult"]


class CourtSearch:
    """Search operations over the court records LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_domboksregister(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        roll: str | None = None,
        socken: str | None = None,
        datum_from: str | None = None,
        datum_till: str | None = None,
        arende: str | None = None,
    ) -> SearchResult:
        """Search the Domboksregister table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            roll: Optional case-insensitive substring filter on roll (e.g. Kärande, Svarande).
            socken: Optional case-insensitive substring filter on socken (parish).
            datum_from: Optional date range start (inclusive, string comparison on datum field, e.g. '1650-01-01').
            datum_till: Optional date range end (inclusive, string comparison on datum field, e.g. '1700-12-31').
            arende: Optional case-insensitive substring filter on case type (arende field).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("roll", roll) if roll else None,
            text_contains("socken", socken) if socken else None,
            at_least("datum", datum_from) if datum_from else None,
            at_most("datum", datum_till) if datum_till else None,
            text_contains("arende", arende) if arende else None,
        )
        return lancedb_fts_search(self._db, DOMBOKSREGISTER_TABLE, keyword, limit=limit, offset=offset, where=where)

    def search_medelstad(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        mal_typ: str | None = None,
        norm_forsamling: str | None = None,
        datum_from: str | None = None,
        datum_till: str | None = None,
    ) -> SearchResult:
        """Search the Medelstad table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            mal_typ: Optional case-insensitive substring filter on case type.
            norm_forsamling: Optional case-insensitive substring filter on parish.
            datum_from: Optional date range start (inclusive, string comparison on ting_dag field, e.g. '1690-01-01').
            datum_till: Optional date range end (inclusive, string comparison on ting_dag field, e.g. '1750-12-31').

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("mal_typ", mal_typ) if mal_typ else None,
            text_contains("norm_forsamling", norm_forsamling) if norm_forsamling else None,
            at_least("ting_dag", datum_from) if datum_from else None,
            at_most("ting_dag", datum_till) if datum_till else None,
        )
        return lancedb_fts_search(self._db, MEDELSTAD_TABLE, keyword, limit=limit, offset=offset, where=where)

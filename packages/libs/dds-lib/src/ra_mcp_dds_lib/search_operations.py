"""Full-text search operations over the DDS LanceDB tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, any_of, at_least, at_most, combine, lancedb_fts_search, text_contains

from .config import DODA_TABLE, FODELSE_TABLE, VIGSEL_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["DDSSearch", "SearchResult"]


class DDSSearch:
    """Search operations over the DDS LanceDB tables (births, deaths, marriages)."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_fodelse(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        forsamling: str | None = None,
        lan: str | None = None,
        kon: str | None = None,
        datum_from: str | None = None,
        datum_till: str | None = None,
    ) -> SearchResult:
        """Search the Födelse (birth) table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            forsamling: Optional case-insensitive substring filter on parish.
            lan: Optional case-insensitive substring filter on county.
            kon: Optional case-insensitive substring filter on gender.
            datum_from: Optional earliest date filter (YYYY-MM-DD, inclusive).
            datum_till: Optional latest date filter (YYYY-MM-DD, inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("forsamling", forsamling) if forsamling else None,
            text_contains("lan", lan) if lan else None,
            text_contains("kon", kon) if kon else None,
            at_least("datum", datum_from) if datum_from else None,
            at_most("datum", datum_till) if datum_till else None,
        )
        return lancedb_fts_search(self._db, FODELSE_TABLE, keyword, limit=limit, offset=offset, where=where)

    def search_doda(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        forsamling: str | None = None,
        lan: str | None = None,
        dodsorsak: str | None = None,
        datum_from: str | None = None,
        datum_till: str | None = None,
    ) -> SearchResult:
        """Search the Döda (death) table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            forsamling: Optional case-insensitive substring filter on parish.
            lan: Optional case-insensitive substring filter on county.
            dodsorsak: Optional case-insensitive substring filter on cause of death.
            datum_from: Optional earliest date filter (YYYY-MM-DD, inclusive).
            datum_till: Optional latest date filter (YYYY-MM-DD, inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("forsamling", forsamling) if forsamling else None,
            text_contains("lan", lan) if lan else None,
            any_of(text_contains("dodsorsak", dodsorsak), text_contains("dodsorsak_klassificerat", dodsorsak)) if dodsorsak else None,
            at_least("datum", datum_from) if datum_from else None,
            at_most("datum", datum_till) if datum_till else None,
        )
        return lancedb_fts_search(self._db, DODA_TABLE, keyword, limit=limit, offset=offset, where=where)

    def search_vigsel(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        forsamling: str | None = None,
        lan: str | None = None,
        datum_from: str | None = None,
        datum_till: str | None = None,
    ) -> SearchResult:
        """Search the Vigsel (marriage) table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            forsamling: Optional case-insensitive substring filter on parish.
            lan: Optional case-insensitive substring filter on county.
            datum_from: Optional earliest date filter (YYYY-MM-DD, inclusive).
            datum_till: Optional latest date filter (YYYY-MM-DD, inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            text_contains("forsamling", forsamling) if forsamling else None,
            text_contains("lan", lan) if lan else None,
            at_least("datum", datum_from) if datum_from else None,
            at_most("datum", datum_till) if datum_till else None,
        )
        return lancedb_fts_search(self._db, VIGSEL_TABLE, keyword, limit=limit, offset=offset, where=where)

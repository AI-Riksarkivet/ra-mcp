"""Full-text search operations over the SBL LanceDB table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, at_least, at_most, combine, equals, lancedb_fts_search, text_contains

from .config import SBL_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["SBLSearch", "SearchResult"]


class SBLSearch:
    """Search operations over the SBL LanceDB table."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        gender: str | None = None,
        occupation: str | None = None,
        birth_place: str | None = None,
        death_place: str | None = None,
        birth_year_min: int | None = None,
        birth_year_max: int | None = None,
        death_year_min: int | None = None,
        death_year_max: int | None = None,
    ) -> SearchResult:
        """Search the SBL table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            gender: Optional exact filter on the gender field.
            occupation: Optional case-insensitive substring filter on occupation.
            birth_place: Optional case-insensitive substring filter on birth_place.
            death_place: Optional case-insensitive substring filter on death_place.
            birth_year_min: Optional minimum birth year (inclusive).
            birth_year_max: Optional maximum birth year (inclusive).
            death_year_min: Optional minimum death year (inclusive).
            death_year_max: Optional maximum death year (inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        where = combine(
            equals("gender", gender) if gender else None,
            text_contains("occupation", occupation) if occupation else None,
            text_contains("birth_place", birth_place) if birth_place else None,
            text_contains("death_place", death_place) if death_place else None,
            at_least("birth_year", birth_year_min) if birth_year_min is not None else None,
            at_most("birth_year", birth_year_max) if birth_year_max is not None else None,
            at_least("death_year", death_year_min) if death_year_min is not None else None,
            at_most("death_year", death_year_max) if death_year_max is not None else None,
        )
        return lancedb_fts_search(self._db, SBL_TABLE, keyword, limit=limit, offset=offset, where=where)

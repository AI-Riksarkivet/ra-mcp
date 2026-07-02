"""Full-text search operations over the Specialsök LanceDB tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import FANGRULLOR_TABLE, FLYGVAPEN_TABLE, KURHUSET_TABLE, PRESS_TABLE, VIDEO_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a Specialsök search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class SpecialsokSearch:
    """Search operations over the Specialsök LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def _search_table(
        self,
        table_name: str,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        filters: dict[str, str | None] | None = None,
    ) -> SearchResult:
        """Generic FTS search with optional case-insensitive substring filters.

        Args:
            table_name: Name of the LanceDB table.
            keyword: Search term (required, non-empty).
            limit: Maximum number of results.
            offset: Pagination offset.
            filters: Dict of field_name -> filter_value (case-insensitive substring).

        Returns:
            SearchResult with matching records.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        active_filters = {k: v for k, v in (filters or {}).items() if v}
        has_filters = bool(active_filters)
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(table_name)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        for field, value in active_filters.items():
            value_lower = value.lower()
            rows = [r for r in rows if value_lower in r.get(field, "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

    def search_flygvapen(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        fpl_typ: str | None = None,
    ) -> SearchResult:
        """Search the Flygvapenhaverier table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            fpl_typ: Optional case-insensitive substring filter on aircraft type.
        """
        return self._search_table(
            FLYGVAPEN_TABLE,
            keyword,
            limit=limit,
            offset=offset,
            filters={"fpl_typ": fpl_typ},
        )

    def search_fangrullor(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        brott: str | None = None,
    ) -> SearchResult:
        """Search the Fångrullor table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            brott: Optional case-insensitive substring filter on crime type.
        """
        return self._search_table(
            FANGRULLOR_TABLE,
            keyword,
            limit=limit,
            offset=offset,
            filters={"brott": brott},
        )

    def search_kurhuset(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        sjukdom: str | None = None,
    ) -> SearchResult:
        """Search the Kurhuset table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            sjukdom: Optional case-insensitive substring filter on disease.
        """
        return self._search_table(
            KURHUSET_TABLE,
            keyword,
            limit=limit,
            offset=offset,
            filters={"sjukdom": sjukdom},
        )

    def search_press(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        aar: str | None = None,
    ) -> SearchResult:
        """Search the Presskonferenser table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            aar: Optional case-insensitive substring filter on year.
        """
        return self._search_table(
            PRESS_TABLE,
            keyword,
            limit=limit,
            offset=offset,
            filters={"aar": aar},
        )

    def search_video(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        laen: str | None = None,
        kommun: str | None = None,
    ) -> SearchResult:
        """Search the Videobutiker table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            laen: Optional case-insensitive substring filter on county.
            kommun: Optional case-insensitive substring filter on municipality.
        """
        return self._search_table(
            VIDEO_TABLE,
            keyword,
            limit=limit,
            offset=offset,
            filters={"laen": laen, "kommun": kommun},
        )

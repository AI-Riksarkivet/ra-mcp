"""Full-text search operations over the Specialsök LanceDB tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import FANGRULLOR_TABLE, FLYGVAPEN_TABLE, KURHUSET_TABLE, PRESS_TABLE, VIDEO_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["SearchResult", "SpecialsokSearch"]


class SpecialsokSearch:
    """Search operations over the Specialsök LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

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
        where = combine(text_contains("fpl_typ", fpl_typ) if fpl_typ else None)
        return lancedb_fts_search(self._db, FLYGVAPEN_TABLE, keyword, limit=limit, offset=offset, where=where)

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
        where = combine(text_contains("brott", brott) if brott else None)
        return lancedb_fts_search(self._db, FANGRULLOR_TABLE, keyword, limit=limit, offset=offset, where=where)

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
        where = combine(text_contains("sjukdom", sjukdom) if sjukdom else None)
        return lancedb_fts_search(self._db, KURHUSET_TABLE, keyword, limit=limit, offset=offset, where=where)

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
        where = combine(text_contains("aar", aar) if aar else None)
        return lancedb_fts_search(self._db, PRESS_TABLE, keyword, limit=limit, offset=offset, where=where)

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
        where = combine(
            text_contains("laen", laen) if laen else None,
            text_contains("kommun", kommun) if kommun else None,
        )
        return lancedb_fts_search(self._db, VIDEO_TABLE, keyword, limit=limit, offset=offset, where=where)

"""Full-text search operations over SDHK and MPO LanceDB tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ra_mcp_dataset_lib import SearchResult, combine, lancedb_fts_search, text_contains

from .config import MPO_TABLE, SDHK_TABLE


if TYPE_CHECKING:
    import lancedb


__all__ = ["DiplomaticsSearch", "SearchResult"]


class DiplomaticsSearch:
    """Search operations over SDHK and MPO LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_sdhk(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        author: str | None = None,
        place: str | None = None,
        language: str | None = None,
    ) -> SearchResult:
        """Search the SDHK table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            author: Optional filter on the author field (case-insensitive substring).
            place: Optional filter on the place field (case-insensitive substring).
            language: Optional filter on the language field (case-insensitive substring).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty.
        """
        where = combine(
            text_contains("author", author) if author else None,
            text_contains("place", place) if place else None,
            text_contains("language", language) if language else None,
        )
        return lancedb_fts_search(self._db, SDHK_TABLE, keyword, limit=limit, offset=offset, where=where)

    def search_mpo(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        category: str | None = None,
        institution: str | None = None,
        script: str | None = None,
    ) -> SearchResult:
        """Search the MPO table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            category: Optional filter on the category field (case-insensitive substring).
            institution: Optional filter on the institution field (case-insensitive substring).
            script: Optional filter on the script field (case-insensitive substring).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty.
        """
        where = combine(
            text_contains("category", category) if category else None,
            text_contains("institution", institution) if institution else None,
            text_contains("script", script) if script else None,
        )
        return lancedb_fts_search(self._db, MPO_TABLE, keyword, limit=limit, offset=offset, where=where)

    def get_sdhk_by_id(self, sdhk_id: int) -> dict | None:
        """Look up a single SDHK record by ID.

        Returns the record dict or None if not found.
        """
        table = self._db.open_table(SDHK_TABLE)
        rows = table.search().where(f"id = {sdhk_id}").limit(1).to_list()
        return rows[0] if rows else None

    def get_mpo_by_id(self, mpo_id: int) -> dict | None:
        """Look up a single MPO record by ID.

        Returns the record dict or None if not found.
        """
        table = self._db.open_table(MPO_TABLE)
        rows = table.search().where(f"id = {mpo_id}").limit(1).to_list()
        return rows[0] if rows else None

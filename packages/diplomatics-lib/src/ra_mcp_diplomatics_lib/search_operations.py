"""Full-text search operations over SDHK and MPO LanceDB tables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .config import MPO_TABLE, SDHK_TABLE

if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a diplomatics search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int
    table_name: str


class DiplomaticsSearch:
    """Search operations over SDHK and MPO LanceDB tables."""

    def __init__(self, db: "lancedb.DBConnection") -> None:
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
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        table = self._db.open_table(SDHK_TABLE)
        rows = (
            table.search(keyword, query_type="fts")
            .limit(limit + offset)
            .to_list()
        )

        # Apply post-filters
        if author:
            author_lower = author.lower()
            rows = [r for r in rows if author_lower in r.get("author", "").lower()]
        if place:
            place_lower = place.lower()
            rows = [r for r in rows if place_lower in r.get("place", "").lower()]
        if language:
            language_lower = language.lower()
            rows = [r for r in rows if language_lower in r.get("language", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
            table_name=SDHK_TABLE,
        )

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
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        table = self._db.open_table(MPO_TABLE)
        rows = (
            table.search(keyword, query_type="fts")
            .limit(limit + offset)
            .to_list()
        )

        # Apply post-filters
        if category:
            category_lower = category.lower()
            rows = [r for r in rows if category_lower in r.get("category", "").lower()]
        if institution:
            institution_lower = institution.lower()
            rows = [r for r in rows if institution_lower in r.get("institution", "").lower()]
        if script:
            script_lower = script.lower()
            rows = [r for r in rows if script_lower in r.get("script", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
            table_name=MPO_TABLE,
        )

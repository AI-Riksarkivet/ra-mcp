"""Full-text search operations over the Rosenberg LanceDB table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import ROSENBERG_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a Rosenberg search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class RosenbergSearch:
    """Search operations over the Rosenberg LanceDB table."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        lan: str | None = None,
        forsamling: str | None = None,
    ) -> SearchResult:
        """Search the Rosenberg table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            lan: Optional case-insensitive substring filter on county (län).
            forsamling: Optional case-insensitive substring filter on parish (församling).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([lan, forsamling])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(ROSENBERG_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        # Apply post-filters
        if lan:
            lan_lower = lan.lower()
            rows = [r for r in rows if lan_lower in r.get("lan", "").lower()]
        if forsamling:
            forsamling_lower = forsamling.lower()
            rows = [r for r in rows if forsamling_lower in r.get("forsamling", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

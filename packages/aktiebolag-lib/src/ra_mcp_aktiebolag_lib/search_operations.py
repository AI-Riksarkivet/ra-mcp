"""Full-text search operations over the Aktiebolag LanceDB tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import BOLAG_TABLE, STYRELSE_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from an Aktiebolag search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


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
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([styrelsesate])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(BOLAG_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if styrelsesate:
            styrelsesate_lower = styrelsesate.lower()
            rows = [r for r in rows if styrelsesate_lower in r.get("styrelsesate", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

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
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([titel])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(STYRELSE_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if titel:
            titel_lower = titel.lower()
            rows = [r for r in rows if titel_lower in r.get("titel", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

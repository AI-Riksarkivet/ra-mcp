"""Full-text search operations over the court records LanceDB tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import DOMBOKSREGISTER_TABLE, MEDELSTAD_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a court records search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


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
    ) -> SearchResult:
        """Search the Domboksregister table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            roll: Optional case-insensitive substring filter on roll (e.g. Kärande, Svarande).
            socken: Optional case-insensitive substring filter on socken (parish).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([roll, socken])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(DOMBOKSREGISTER_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if roll:
            roll_lower = roll.lower()
            rows = [r for r in rows if roll_lower in r.get("roll", "").lower()]
        if socken:
            socken_lower = socken.lower()
            rows = [r for r in rows if socken_lower in r.get("socken", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

    def search_medelstad(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        mal_typ: str | None = None,
        norm_forsamling: str | None = None,
    ) -> SearchResult:
        """Search the Medelstad table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            mal_typ: Optional case-insensitive substring filter on case type.
            norm_forsamling: Optional case-insensitive substring filter on parish.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([mal_typ, norm_forsamling])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(MEDELSTAD_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if mal_typ:
            mal_typ_lower = mal_typ.lower()
            rows = [r for r in rows if mal_typ_lower in r.get("mal_typ", "").lower()]
        if norm_forsamling:
            norm_forsamling_lower = norm_forsamling.lower()
            rows = [r for r in rows if norm_forsamling_lower in r.get("norm_forsamling", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

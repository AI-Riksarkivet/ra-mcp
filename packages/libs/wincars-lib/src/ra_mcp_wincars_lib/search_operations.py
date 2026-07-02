"""Full-text search operations over the Wincars LanceDB table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import WINCARS_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a Wincars search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class WincarsSearch:
    """Search operations over the Wincars LanceDB table (vehicle registrations)."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        typ: str | None = None,
        hemvist: str | None = None,
        fabrikat: str | None = None,
    ) -> SearchResult:
        """Search the Wincars table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            typ: Optional case-insensitive substring filter on vehicle type (PB, MC, LB, etc.).
            hemvist: Optional case-insensitive substring filter on domicile/location.
            fabrikat: Optional case-insensitive substring filter on make/manufacturer.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([typ, hemvist, fabrikat])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(WINCARS_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if typ:
            typ_lower = typ.lower()
            rows = [r for r in rows if typ_lower in r.get("typ", "").lower()]
        if hemvist:
            hemvist_lower = hemvist.lower()
            rows = [r for r in rows if hemvist_lower in r.get("hemvist", "").lower()]
        if fabrikat:
            fabrikat_lower = fabrikat.lower()
            rows = [r for r in rows if fabrikat_lower in r.get("fabrikat", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

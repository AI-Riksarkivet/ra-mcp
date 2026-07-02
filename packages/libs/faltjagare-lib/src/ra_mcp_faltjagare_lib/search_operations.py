"""Full-text search operations over the Fältjägare LanceDB table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import FALTJAGARE_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a Fältjägare search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class FaltjagareSearch:
    """Search operations over the Fältjägare LanceDB table."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        kompani: str | None = None,
        region: str | None = None,
        befattning: str | None = None,
    ) -> SearchResult:
        """Search the Fältjägare table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            kompani: Optional case-insensitive substring filter on kompani (company).
            region: Optional case-insensitive substring filter on region.
            befattning: Optional case-insensitive substring filter on befattning (rank).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([kompani, region, befattning])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(FALTJAGARE_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        # Apply post-filters
        if kompani:
            kompani_lower = kompani.lower()
            rows = [r for r in rows if kompani_lower in r.get("kompani", "").lower()]
        if region:
            region_lower = region.lower()
            rows = [r for r in rows if region_lower in r.get("region", "").lower()]
        if befattning:
            befattning_lower = befattning.lower()
            rows = [r for r in rows if befattning_lower in r.get("befattning", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

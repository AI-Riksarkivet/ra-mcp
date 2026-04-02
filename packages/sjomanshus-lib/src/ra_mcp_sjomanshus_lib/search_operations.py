"""Full-text search operations over the Sjömanshus LanceDB tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import LIGGARE_TABLE, MATRIKEL_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a Sjömanshus search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class SjomanshusSearch:
    """Search operations over the Sjömanshus LanceDB tables."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_liggare(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        befattning: str | None = None,
        fartyg: str | None = None,
        sjoemanshus: str | None = None,
        hemmahamn: str | None = None,
        kapten: str | None = None,
        redare: str | None = None,
        destination: str | None = None,
    ) -> SearchResult:
        """Search the Liggare table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            befattning: Optional case-insensitive substring filter on befattning_yrke.
            fartyg: Optional case-insensitive substring filter on fartyg.
            sjoemanshus: Optional case-insensitive substring filter on sjoemanshus.
            hemmahamn: Optional case-insensitive substring filter on hemmahamn.
            kapten: Optional case-insensitive substring filter on kapten.
            redare: Optional case-insensitive substring filter on redare.
            destination: Optional case-insensitive substring filter on destination.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([befattning, fartyg, sjoemanshus, hemmahamn, kapten, redare, destination])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(LIGGARE_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        # Apply post-filters
        if befattning:
            befattning_lower = befattning.lower()
            rows = [r for r in rows if befattning_lower in r.get("befattning_yrke", "").lower()]
        if fartyg:
            fartyg_lower = fartyg.lower()
            rows = [r for r in rows if fartyg_lower in r.get("fartyg", "").lower()]
        if sjoemanshus:
            sjoemanshus_lower = sjoemanshus.lower()
            rows = [r for r in rows if sjoemanshus_lower in r.get("sjoemanshus", "").lower()]
        if hemmahamn:
            hemmahamn_lower = hemmahamn.lower()
            rows = [r for r in rows if hemmahamn_lower in r.get("hemmahamn", "").lower()]
        if kapten:
            kapten_lower = kapten.lower()
            rows = [r for r in rows if kapten_lower in r.get("kapten", "").lower()]
        if redare:
            redare_lower = redare.lower()
            rows = [r for r in rows if redare_lower in r.get("redare", "").lower()]
        if destination:
            destination_lower = destination.lower()
            rows = [r for r in rows if destination_lower in r.get("destination", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

    def search_matrikel(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        sjoemanshus: str | None = None,
    ) -> SearchResult:
        """Search the Matrikel table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            sjoemanshus: Optional case-insensitive substring filter on sjoemanshus.

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([sjoemanshus])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(MATRIKEL_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        # Apply post-filters
        if sjoemanshus:
            sjoemanshus_lower = sjoemanshus.lower()
            rows = [r for r in rows if sjoemanshus_lower in r.get("sjoemanshus", "").lower()]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

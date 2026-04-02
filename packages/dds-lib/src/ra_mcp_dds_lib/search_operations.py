"""Full-text search operations over the DDS LanceDB tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import DODA_TABLE, FODELSE_TABLE, VIGSEL_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from a DDS search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class DDSSearch:
    """Search operations over the DDS LanceDB tables (births, deaths, marriages)."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search_fodelse(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        forsamling: str | None = None,
        lan: str | None = None,
        kon: str | None = None,
        datum_from: str | None = None,
        datum_till: str | None = None,
    ) -> SearchResult:
        """Search the Födelse (birth) table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            forsamling: Optional case-insensitive substring filter on parish.
            lan: Optional case-insensitive substring filter on county.
            kon: Optional case-insensitive substring filter on gender.
            datum_from: Optional earliest date filter (YYYY-MM-DD, inclusive).
            datum_till: Optional latest date filter (YYYY-MM-DD, inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([forsamling, lan, kon, datum_from, datum_till])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(FODELSE_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if forsamling:
            forsamling_lower = forsamling.lower()
            rows = [r for r in rows if forsamling_lower in r.get("forsamling", "").lower()]
        if lan:
            lan_lower = lan.lower()
            rows = [r for r in rows if lan_lower in r.get("lan", "").lower()]
        if kon:
            kon_lower = kon.lower()
            rows = [r for r in rows if kon_lower in r.get("kon", "").lower()]
        if datum_from:
            rows = [r for r in rows if r.get("datum", "") >= datum_from]
        if datum_till:
            rows = [r for r in rows if r.get("datum", "") <= datum_till]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

    def search_doda(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        forsamling: str | None = None,
        lan: str | None = None,
        dodsorsak: str | None = None,
        datum_from: str | None = None,
        datum_till: str | None = None,
    ) -> SearchResult:
        """Search the Döda (death) table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            forsamling: Optional case-insensitive substring filter on parish.
            lan: Optional case-insensitive substring filter on county.
            dodsorsak: Optional case-insensitive substring filter on cause of death.
            datum_from: Optional earliest date filter (YYYY-MM-DD, inclusive).
            datum_till: Optional latest date filter (YYYY-MM-DD, inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([forsamling, lan, dodsorsak, datum_from, datum_till])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(DODA_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if forsamling:
            forsamling_lower = forsamling.lower()
            rows = [r for r in rows if forsamling_lower in r.get("forsamling", "").lower()]
        if lan:
            lan_lower = lan.lower()
            rows = [r for r in rows if lan_lower in r.get("lan", "").lower()]
        if dodsorsak:
            dodsorsak_lower = dodsorsak.lower()
            rows = [r for r in rows if dodsorsak_lower in r.get("dodsorsak", "").lower() or dodsorsak_lower in r.get("dodsorsak_klassificerat", "").lower()]
        if datum_from:
            rows = [r for r in rows if r.get("datum", "") >= datum_from]
        if datum_till:
            rows = [r for r in rows if r.get("datum", "") <= datum_till]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

    def search_vigsel(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        forsamling: str | None = None,
        lan: str | None = None,
        datum_from: str | None = None,
        datum_till: str | None = None,
    ) -> SearchResult:
        """Search the Vigsel (marriage) table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            forsamling: Optional case-insensitive substring filter on parish.
            lan: Optional case-insensitive substring filter on county.
            datum_from: Optional earliest date filter (YYYY-MM-DD, inclusive).
            datum_till: Optional latest date filter (YYYY-MM-DD, inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([forsamling, lan, datum_from, datum_till])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(VIGSEL_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        if forsamling:
            forsamling_lower = forsamling.lower()
            rows = [r for r in rows if forsamling_lower in r.get("forsamling", "").lower()]
        if lan:
            lan_lower = lan.lower()
            rows = [r for r in rows if lan_lower in r.get("lan", "").lower()]
        if datum_from:
            rows = [r for r in rows if r.get("datum", "") >= datum_from]
        if datum_till:
            rows = [r for r in rows if r.get("datum", "") <= datum_till]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

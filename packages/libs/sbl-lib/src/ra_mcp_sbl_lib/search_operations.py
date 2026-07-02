"""Full-text search operations over the SBL LanceDB table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import SBL_TABLE


if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from an SBL search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class SBLSearch:
    """Search operations over the SBL LanceDB table."""

    def __init__(self, db: lancedb.DBConnection) -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        gender: str | None = None,
        occupation: str | None = None,
        birth_place: str | None = None,
        death_place: str | None = None,
        birth_year_min: int | None = None,
        birth_year_max: int | None = None,
        death_year_min: int | None = None,
        death_year_max: int | None = None,
    ) -> SearchResult:
        """Search the SBL table using full-text search.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            gender: Optional exact filter on the gender field.
            occupation: Optional case-insensitive substring filter on occupation.
            birth_place: Optional case-insensitive substring filter on birth_place.
            death_place: Optional case-insensitive substring filter on death_place.
            birth_year_min: Optional minimum birth year (inclusive).
            birth_year_max: Optional maximum birth year (inclusive).
            death_year_min: Optional minimum death year (inclusive).
            death_year_max: Optional maximum death year (inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty or whitespace.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([gender, occupation, birth_place, death_place, birth_year_min, birth_year_max, death_year_min, death_year_max])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(SBL_TABLE)
        rows = table.search(keyword, query_type="fts").limit(fetch_limit).to_list()

        # Apply post-filters
        if gender:
            rows = [r for r in rows if r.get("gender", "") == gender]
        if occupation:
            occupation_lower = occupation.lower()
            rows = [r for r in rows if occupation_lower in r.get("occupation", "").lower()]
        if birth_place:
            birth_place_lower = birth_place.lower()
            rows = [r for r in rows if birth_place_lower in r.get("birth_place", "").lower()]
        if death_place:
            death_place_lower = death_place.lower()
            rows = [r for r in rows if death_place_lower in r.get("death_place", "").lower()]
        if birth_year_min is not None:
            rows = [r for r in rows if r.get("birth_year") is not None and r["birth_year"] >= birth_year_min]
        if birth_year_max is not None:
            rows = [r for r in rows if r.get("birth_year") is not None and r["birth_year"] <= birth_year_max]
        if death_year_min is not None:
            rows = [r for r in rows if r.get("death_year") is not None and r["death_year"] >= death_year_min]
        if death_year_max is not None:
            rows = [r for r in rows if r.get("death_year") is not None and r["death_year"] <= death_year_max]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )

"""MCP tool for searching Svenskt biografiskt lexikon (SBL)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_sbl_lib import SBLSearch
from ra_mcp_sbl_lib.config import LANCEDB_URI

from .formatter import format_sbl_results


logger = logging.getLogger("ra_mcp.sbl.sbl_tool")

# Lazy-init LanceDB connection
_db = None


def _get_db() -> lancedb.DBConnection:
    """Return a cached LanceDB connection, opening it on first use."""
    global _db
    if _db is None:
        import lancedb

        logger.info("Opening LanceDB at %s", LANCEDB_URI)
        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_sbl_tool(mcp) -> None:
    """Register the search_sbl MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_sbl",
        tags={"sbl", "biography", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Svenskt biografiskt lexikon (SBL) — 9,400+ articles about notable people "
            "in Swedish history. Returns name, occupation, career details and credentials (CV/meriter), "
            "birth/death dates and places, sources, and portrait image URLs. "
            "The full biographical narrative is only available on the SBL website (linked via SBL URI in results). "
            "Covers medieval to 20th century. Articles go up to letter S (T to O not yet published). "
            "Filter by gender, occupation, place, or year range. Paginate with offset (0, 25, 50, ...)."
        ),
    )
    async def search_sbl(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across SBL biographical articles."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        gender: Annotated[
            str | None,
            Field(description="Optional filter: m (male), f (female), or - (family/other). Exact match."),
        ] = None,
        occupation: Annotated[
            str | None,
            Field(description="Optional filter: only return articles with this occupation (case-insensitive substring match)."),
        ] = None,
        birth_place: Annotated[
            str | None,
            Field(description="Optional filter: only return articles with this birth place (case-insensitive substring match)."),
        ] = None,
        death_place: Annotated[
            str | None,
            Field(description="Optional filter: only return articles with this death place (case-insensitive substring match)."),
        ] = None,
        birth_year_min: Annotated[
            int | None,
            Field(description="Optional filter: minimum birth year (inclusive)."),
        ] = None,
        birth_year_max: Annotated[
            int | None,
            Field(description="Optional filter: maximum birth year (inclusive)."),
        ] = None,
        death_year_min: Annotated[
            int | None,
            Field(description="Optional filter: minimum death year (inclusive)."),
        ] = None,
        death_year_max: Annotated[
            int | None,
            Field(description="Optional filter: maximum death year (inclusive)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search SBL biographical articles using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Linné'."

        if research_context:
            logger.info("search_sbl | context: %s", research_context)
        logger.info("search_sbl called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SBLSearch(db)
            result = searcher.search(
                keyword,
                limit=limit,
                offset=offset,
                gender=gender,
                occupation=occupation,
                birth_place=birth_place,
                death_place=death_place,
                birth_year_min=birth_year_min,
                birth_year_max=birth_year_max,
                death_year_min=death_year_min,
                death_year_max=death_year_max,
            )
            return format_sbl_results(result)

        except Exception as exc:
            logger.error("search_sbl failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: SBL search failed \u2014 {exc!s}"

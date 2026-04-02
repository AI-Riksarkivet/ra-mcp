"""MCP tool for searching Domboksregister (Västra härad court records)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_court_lib import CourtSearch
from ra_mcp_court_lib.config import LANCEDB_URI

from .formatter import format_domboksregister_results


logger = logging.getLogger("ra_mcp.court.domboksregister_tool")

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


def register_domboksregister_tool(mcp) -> None:
    """Register the search_domboksregister MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_domboksregister",
        tags={"court", "domboksregister", "legal", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Västra härad court records 1611-1730 — 88,000 persons in court cases. "
            "Returns person name, role (plaintiff/defendant), title, parish, place, case notes, "
            "date, and case type."
        ),
    )
    async def search_domboksregister(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across Domboksregister court records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        roll: Annotated[
            str | None,
            Field(description="Optional filter: role in case (case-insensitive substring match, e.g. 'Kärande' for plaintiff, 'Svarande' for defendant)."),
        ] = None,
        socken: Annotated[
            str | None,
            Field(description="Optional filter: parish name (case-insensitive substring match)."),
        ] = None,
        datum_from: Annotated[
            str | None,
            Field(description="Optional filter: date range start inclusive (e.g. '1650-01-01'). String comparison on datum field."),
        ] = None,
        datum_till: Annotated[
            str | None,
            Field(description="Optional filter: date range end inclusive (e.g. '1700-12-31'). String comparison on datum field."),
        ] = None,
        arende: Annotated[
            str | None,
            Field(description="Optional filter: case type (case-insensitive substring match on arende field, e.g. 'Skuld', 'Våld')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Domboksregister court records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_domboksregister | context: %s", research_context)
        logger.info("search_domboksregister called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = CourtSearch(db)
            result = searcher.search_domboksregister(
                keyword,
                limit=limit,
                offset=offset,
                roll=roll,
                socken=socken,
                datum_from=datum_from,
                datum_till=datum_till,
                arende=arende,
            )
            return format_domboksregister_results(result)

        except Exception as exc:
            logger.error("search_domboksregister failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Domboksregister search failed \u2014 {exc!s}"

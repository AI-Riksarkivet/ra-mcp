"""MCP tool for searching Flygvapenhaverier (Swedish military aviation accidents)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from ra_mcp_specialsok_lib import SpecialsokSearch
from ra_mcp_specialsok_lib.config import LANCEDB_URI

from .formatter import format_flygvapen_results


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger("ra_mcp.specialsok.flygvapen_tool")

_db = None


def _get_db() -> lancedb.DBConnection:
    """Return a cached LanceDB connection, opening it on first use."""
    global _db
    if _db is None:
        import lancedb

        logger.info("Opening LanceDB at %s", LANCEDB_URI)
        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_flygvapen_tool(mcp) -> None:
    """Register the search_flygvapen MCP tool."""

    @mcp.tool(
        name="search_flygvapen",
        tags={"specialsok", "flygvapen", "military", "aviation", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=("Search Swedish military aviation accidents 1912-2007 — 2,400 incidents with aircraft types, crash sites, and summaries."),
    )
    async def search_flygvapen(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across aviation accident records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        fpl_typ: Annotated[
            str | None,
            Field(description="Optional filter: aircraft type (case-insensitive substring match, e.g. 'J 35' for Draken)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish military aviation accident records."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Draken'."

        if research_context:
            logger.info("search_flygvapen | context: %s", research_context)
        logger.info("search_flygvapen called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SpecialsokSearch(db)
            result = searcher.search_flygvapen(keyword, limit=limit, offset=offset, fpl_typ=fpl_typ)
            return format_flygvapen_results(result)
        except Exception as exc:
            logger.error("search_flygvapen failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Flygvapen search failed \u2014 {exc!s}"

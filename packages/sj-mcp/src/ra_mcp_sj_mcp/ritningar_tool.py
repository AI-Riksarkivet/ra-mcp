"""MCP tool for searching FIRA/SIRA railway technical drawings."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_sj_lib import SJSearch
from ra_mcp_sj_lib.config import LANCEDB_URI

from .formatter import format_ritningar_results


logger = logging.getLogger("ra_mcp.sj.ritningar_tool")

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


def register_ritningar_tool(mcp) -> None:
    """Register the search_ritningar MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_ritningar",
        tags={"sj", "fira", "sira", "railway", "drawings", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search SJ railway technical drawings — 118,000 drawings of stations, buildings, and infrastructure. "
            "Returns station/building name, description, drawing number, date, format, district, and building type."
        ),
    )
    async def search_ritningar(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across FIRA/SIRA railway drawing records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        dkod: Annotated[
            str | None,
            Field(description="Optional filter: district code (case-insensitive substring match)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search FIRA/SIRA railway technical drawings using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'GÖTEBORG'."

        if research_context:
            logger.info("search_ritningar | context: %s", research_context)
        logger.info("search_ritningar called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SJSearch(db)
            result = searcher.search_ritningar(
                keyword,
                limit=limit,
                offset=offset,
                dkod=dkod,
            )
            return format_ritningar_results(result)

        except Exception as exc:
            logger.error("search_ritningar failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Ritningar search failed \u2014 {exc!s}"

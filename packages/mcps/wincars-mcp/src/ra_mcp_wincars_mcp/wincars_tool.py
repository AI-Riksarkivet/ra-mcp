"""MCP tool for searching Wincars (Norrland vehicle registration) records."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_wincars_lib import WincarsSearch
from ra_mcp_wincars_lib.config import LANCEDB_URI

from .formatter import format_wincars_results


logger = logging.getLogger("ra_mcp.wincars.wincars_tool")

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


def register_wincars_tool(mcp) -> None:
    """Register the search_wincars MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_wincars",
        tags={"wincars", "vehicle", "registration", "norrland", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Norrland vehicle register 1916-1972 — 1.5 million vehicles across 5 northern Swedish counties. "
            "Returns registration number, vehicle type, make/model, year, chassis/engine numbers, "
            "registration/deregistration dates, domicile, and status (active/written off/scrapped)."
        ),
    )
    async def search_wincars(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across vehicle registration records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        typ: Annotated[
            str | None,
            Field(
                description="Optional filter: vehicle type code (case-insensitive, e.g. 'PB'=car, 'MC'=motorcycle, 'LB'=truck, 'SL'=trailer, 'TR'=tractor, 'BS'=bus)."
            ),
        ] = None,
        hemvist: Annotated[
            str | None,
            Field(description="Optional filter: domicile/location (case-insensitive substring match, e.g. 'Sundsvall', 'Umeå')."),
        ] = None,
        fabrikat: Annotated[
            str | None,
            Field(description="Optional filter: make/manufacturer (case-insensitive substring match, e.g. 'Volvo', 'Ford', 'Saab')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Norrland vehicle registration records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Volvo'."

        if research_context:
            logger.info("search_wincars | context: %s", research_context)
        logger.info("search_wincars called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = WincarsSearch(db)
            result = searcher.search(
                keyword,
                limit=limit,
                offset=offset,
                typ=typ,
                hemvist=hemvist,
                fabrikat=fabrikat,
            )
            return format_wincars_results(result)

        except Exception as exc:
            logger.error("search_wincars failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Wincars search failed \u2014 {exc!s}"

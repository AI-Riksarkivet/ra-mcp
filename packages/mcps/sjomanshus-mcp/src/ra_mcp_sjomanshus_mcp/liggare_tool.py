"""MCP tool for searching Sjömanshus Liggare (voyage records)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_sjomanshus_lib import SjomanshusSearch
from ra_mcp_sjomanshus_lib.config import LANCEDB_URI

from .formatter import format_liggare_results


logger = logging.getLogger("ra_mcp.sjomanshus.liggare_tool")

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


def register_liggare_tool(mcp) -> None:
    """Register the search_liggare MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_liggare",
        tags={"sjomanshus", "liggare", "voyage", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Swedish seamen's voyage records (Liggare) — 637,000 individual voyages from 1700s-1900s. "
            "Returns seaman name, rank, ship, home port, destination, captain, shipowner. "
            "Filter by occupation, ship, seamen's house, home port, captain, shipowner, or destination."
        ),
    )
    async def search_liggare(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across Liggare voyage records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        befattning: Annotated[
            str | None,
            Field(description="Optional filter: occupation/rank (case-insensitive substring match, e.g. 'matros', 'styrman')."),
        ] = None,
        fartyg: Annotated[
            str | None,
            Field(description="Optional filter: ship name (case-insensitive substring match)."),
        ] = None,
        sjoemanshus: Annotated[
            str | None,
            Field(description="Optional filter: seamen's house name (case-insensitive substring match, e.g. 'Göteborg', 'Stockholm')."),
        ] = None,
        hemmahamn: Annotated[
            str | None,
            Field(description="Optional filter: home port (case-insensitive substring match)."),
        ] = None,
        kapten: Annotated[
            str | None,
            Field(description="Optional filter: captain name (case-insensitive substring match)."),
        ] = None,
        redare: Annotated[
            str | None,
            Field(description="Optional filter: shipowner name (case-insensitive substring match)."),
        ] = None,
        destination: Annotated[
            str | None,
            Field(description="Optional filter: voyage destination (case-insensitive substring match, e.g. 'Medelhavet', 'Nordamerika')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Sjömanshus Liggare voyage records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_liggare | context: %s", research_context)
        logger.info("search_liggare called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SjomanshusSearch(db)
            result = searcher.search_liggare(
                keyword,
                limit=limit,
                offset=offset,
                befattning=befattning,
                fartyg=fartyg,
                sjoemanshus=sjoemanshus,
                hemmahamn=hemmahamn,
                kapten=kapten,
                redare=redare,
                destination=destination,
            )
            return format_liggare_results(result)

        except Exception as exc:
            logger.error("search_liggare failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Liggare search failed \u2014 {exc!s}"

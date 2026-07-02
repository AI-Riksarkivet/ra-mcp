"""MCP tool for searching Sjömanshus Matrikel (registration records)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_sjomanshus_lib import SjomanshusSearch
from ra_mcp_sjomanshus_lib.config import LANCEDB_URI

from .formatter import format_matrikel_results


logger = logging.getLogger("ra_mcp.sjomanshus.matrikel_tool")

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


def register_matrikel_tool(mcp) -> None:
    """Register the search_matrikel MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_matrikel",
        tags={"sjomanshus", "matrikel", "registration", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Swedish seamen's registration records (Matrikel) — 51,000 registrations. "
            "Returns seaman name, birth info, parents, home parish, registration/deregistration dates."
        ),
    )
    async def search_matrikel(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across Matrikel registration records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        sjoemanshus: Annotated[
            str | None,
            Field(description="Optional filter: seamen's house name (case-insensitive substring match, e.g. 'Göteborg', 'Stockholm')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Sjömanshus Matrikel registration records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_matrikel | context: %s", research_context)
        logger.info("search_matrikel called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SjomanshusSearch(db)
            result = searcher.search_matrikel(
                keyword,
                limit=limit,
                offset=offset,
                sjoemanshus=sjoemanshus,
            )
            return format_matrikel_results(result)

        except Exception as exc:
            logger.error("search_matrikel failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Matrikel search failed \u2014 {exc!s}"

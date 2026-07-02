"""MCP tool for searching Rosenberg's geographical lexicon of Sweden."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_rosenberg_lib import RosenbergSearch
from ra_mcp_rosenberg_lib.config import LANCEDB_URI

from .formatter import format_rosenberg_results


logger = logging.getLogger("ra_mcp.rosenberg.rosenberg_tool")

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


def register_rosenberg_tool(mcp) -> None:
    """Register the search_rosenberg MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_rosenberg",
        tags={"rosenberg", "geography", "places", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Rosenberg's geographical lexicon of Sweden — 66,000 historical places with descriptions. "
            "Returns place name, parish, hundred, county, full description text, and industry/feature flags. "
            "Use for looking up historical Swedish places, parishes, and their descriptions."
        ),
    )
    async def search_rosenberg(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across Rosenberg's geographical lexicon."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        lan: Annotated[
            str | None,
            Field(description="Optional filter: county/län (case-insensitive substring match, e.g. 'Stockholms', 'Malmöhus')."),
        ] = None,
        forsamling: Annotated[
            str | None,
            Field(description="Optional filter: parish/församling (case-insensitive substring match, e.g. 'Klara', 'Hedvig')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Rosenberg's geographical lexicon using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Stockholm'."

        if research_context:
            logger.info("search_rosenberg | context: %s", research_context)
        logger.info("search_rosenberg called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = RosenbergSearch(db)
            result = searcher.search(
                keyword,
                limit=limit,
                offset=offset,
                lan=lan,
                forsamling=forsamling,
            )
            return format_rosenberg_results(result)

        except Exception as exc:
            logger.error("search_rosenberg failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Rosenberg search failed \u2014 {exc!s}"

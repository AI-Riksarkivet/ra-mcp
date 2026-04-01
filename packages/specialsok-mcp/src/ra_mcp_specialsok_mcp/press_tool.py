"""MCP tool for searching Presskonferenser (government press conferences)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from ra_mcp_specialsok_lib import SpecialsokSearch
from ra_mcp_specialsok_lib.config import LANCEDB_URI

from .formatter import format_press_results


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger("ra_mcp.specialsok.press_tool")

_db = None


def _get_db() -> lancedb.DBConnection:
    """Return a cached LanceDB connection, opening it on first use."""
    global _db
    if _db is None:
        import lancedb

        logger.info("Opening LanceDB at %s", LANCEDB_URI)
        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_press_tool(mcp) -> None:
    """Register the search_press MCP tool."""

    @mcp.tool(
        name="search_press",
        tags={"specialsok", "press", "government", "media", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=("Search Swedish government press conferences 1993-2017 — 5,700 conferences with titles and content descriptions."),
    )
    async def search_press(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across press conference records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        aar: Annotated[
            str | None,
            Field(description="Optional filter: year (case-insensitive substring match, e.g. '2005')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish government press conference records."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'EU'."

        if research_context:
            logger.info("search_press | context: %s", research_context)
        logger.info("search_press called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SpecialsokSearch(db)
            result = searcher.search_press(keyword, limit=limit, offset=offset, aar=aar)
            return format_press_results(result)
        except Exception as exc:
            logger.error("search_press failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Press search failed \u2014 {exc!s}"

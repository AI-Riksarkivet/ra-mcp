"""MCP tool for searching Fångrullor (Östersund prison records)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated

from pydantic import Field

from ra_mcp_specialsok_lib import SpecialsokSearch
from ra_mcp_specialsok_lib.config import LANCEDB_URI

from .formatter import format_fangrullor_results


if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger("ra_mcp.specialsok.fangrullor_tool")

_db = None


def _get_db() -> lancedb.DBConnection:
    """Return a cached LanceDB connection, opening it on first use."""
    global _db
    if _db is None:
        import lancedb

        logger.info("Opening LanceDB at %s", LANCEDB_URI)
        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_fangrullor_tool(mcp) -> None:
    """Register the search_fangrullor MCP tool."""

    @mcp.tool(
        name="search_fangrullor",
        tags={"specialsok", "fangrullor", "prison", "criminal", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=("Search Östersund prison records 1810-1900 — 11,500 inmates with names, ages, crimes, and home parishes."),
    )
    async def search_fangrullor(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across prison records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        brott: Annotated[
            str | None,
            Field(description="Optional filter: crime type (case-insensitive substring match, e.g. 'stöld' for theft)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Östersund prison records."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'stöld'."

        if research_context:
            logger.info("search_fangrullor | context: %s", research_context)
        logger.info("search_fangrullor called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SpecialsokSearch(db)
            result = searcher.search_fangrullor(keyword, limit=limit, offset=offset, brott=brott)
            return format_fangrullor_results(result)
        except Exception as exc:
            logger.error("search_fangrullor failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Fångrullor search failed \u2014 {exc!s}"

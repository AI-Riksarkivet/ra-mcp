"""MCP tool for searching Swedish death records (Döda)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_dds_lib import DDSSearch
from ra_mcp_dds_lib.config import LANCEDB_URI

from .formatter import format_doda_results


logger = logging.getLogger("ra_mcp.dds.doda_tool")

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


def register_doda_tool(mcp) -> None:
    """Register the search_doda MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_doda",
        tags={"dds", "church", "death", "genealogy", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Swedish death records — 950,000 records from 1600s-1951. "
            "Returns name, occupation, home parish, age, cause of death, "
            "relative information, and archive reference."
        ),
    )
    async def search_doda(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across death records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        forsamling: Annotated[
            str | None,
            Field(description="Optional filter: parish name (case-insensitive substring match)."),
        ] = None,
        lan: Annotated[
            str | None,
            Field(description="Optional filter: county name (case-insensitive substring match)."),
        ] = None,
        dodsorsak: Annotated[
            str | None,
            Field(description="Optional filter: cause of death (case-insensitive substring match)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish death records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_doda | context: %s", research_context)
        logger.info("search_doda called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = DDSSearch(db)
            result = searcher.search_doda(
                keyword,
                limit=limit,
                offset=offset,
                forsamling=forsamling,
                lan=lan,
                dodsorsak=dodsorsak,
            )
            return format_doda_results(result)

        except Exception as exc:
            logger.error("search_doda failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: D\u00f6da search failed \u2014 {exc!s}"

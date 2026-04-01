"""MCP tool for searching Swedish birth/baptism records (Födelse)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_dds_lib import DDSSearch
from ra_mcp_dds_lib.config import LANCEDB_URI

from .formatter import format_fodelse_results


logger = logging.getLogger("ra_mcp.dds.fodelse_tool")

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


def register_fodelse_tool(mcp) -> None:
    """Register the search_fodelse MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_fodelse",
        tags={"dds", "church", "birth", "genealogy", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Swedish birth/baptism records — 1.3 million records from 1600s-1914. "
            "Returns child name, gender, parents (father/mother names, occupations), "
            "birth/baptism date, parish, county, and birth place."
        ),
    )
    async def search_fodelse(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across birth/baptism records."),
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
        kon: Annotated[
            str | None,
            Field(description="Optional filter: gender (case-insensitive substring match, e.g. 'Man' or 'Kvinna')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish birth/baptism records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_fodelse | context: %s", research_context)
        logger.info("search_fodelse called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = DDSSearch(db)
            result = searcher.search_fodelse(
                keyword,
                limit=limit,
                offset=offset,
                forsamling=forsamling,
                lan=lan,
                kon=kon,
            )
            return format_fodelse_results(result)

        except Exception as exc:
            logger.error("search_fodelse failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Födelse search failed \u2014 {exc!s}"

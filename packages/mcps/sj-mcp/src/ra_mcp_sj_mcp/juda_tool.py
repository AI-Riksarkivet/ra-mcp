"""MCP tool for searching JUDA railway property register."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_sj_lib import SJSearch
from ra_mcp_sj_lib.config import LANCEDB_URI

from .formatter import format_juda_results


logger = logging.getLogger("ra_mcp.sj.juda_tool")

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


def register_juda_tool(mcp) -> None:
    """Register the search_juda MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_juda",
        tags={"sj", "juda", "railway", "property", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search SJ railway property register — 198,000 properties managed by Swedish State Railways. "
            "Returns property description, county, municipality, owner, and notes."
        ),
    )
    async def search_juda(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across JUDA railway property records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        fbagrkod2: Annotated[
            str | None,
            Field(description="Optional filter: owner code (case-insensitive substring match, e.g. 'Jernhusen')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search JUDA railway property register using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'ÄSPINGEN'."

        if research_context:
            logger.info("search_juda | context: %s", research_context)
        logger.info("search_juda called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SJSearch(db)
            result = searcher.search_juda(
                keyword,
                limit=limit,
                offset=offset,
                fbagrkod2=fbagrkod2,
            )
            return format_juda_results(result)

        except Exception as exc:
            logger.error("search_juda failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: JUDA search failed \u2014 {exc!s}"

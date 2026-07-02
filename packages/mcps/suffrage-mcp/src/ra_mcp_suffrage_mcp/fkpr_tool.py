"""MCP tool for searching FKPR (Gothenburg suffrage association 1911-1920)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_suffrage_lib import SuffrageSearch
from ra_mcp_suffrage_lib.config import LANCEDB_URI

from .formatter import format_fkpr_results


logger = logging.getLogger("ra_mcp.suffrage.fkpr_tool")

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


def register_fkpr_tool(mcp) -> None:
    """Register the search_fkpr MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_fkpr",
        tags={"suffrage", "fkpr", "association", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Gothenburg FKPR suffrage association members 1911-1920 — 1,700 women. Returns name, title/occupation, address, and years of membership."
        ),
    )
    async def search_fkpr(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across FKPR membership records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search FKPR Gothenburg suffrage association records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_fkpr | context: %s", research_context)
        logger.info("search_fkpr called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SuffrageSearch(db)
            result = searcher.search_fkpr(
                keyword,
                limit=limit,
                offset=offset,
            )
            return format_fkpr_results(result)

        except Exception as exc:
            logger.error("search_fkpr failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: FKPR search failed \u2014 {exc!s}"

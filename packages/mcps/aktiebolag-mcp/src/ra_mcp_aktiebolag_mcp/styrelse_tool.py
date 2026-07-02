"""MCP tool for searching Styrelsemedlemmar (board members of Swedish companies)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_aktiebolag_lib import AktiebolagSearch
from ra_mcp_aktiebolag_lib.config import LANCEDB_URI

from .formatter import format_styrelse_results


logger = logging.getLogger("ra_mcp.aktiebolag.styrelse_tool")

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


def register_styrelse_tool(mcp) -> None:
    """Register the search_styrelse MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_styrelse",
        tags={"aktiebolag", "board", "director", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=("Search board members of Swedish companies 1901-1935 — 49,000 board members. Returns member name, title, gender, and company name."),
    )
    async def search_styrelse(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across board member records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        titel: Annotated[
            str | None,
            Field(description="Optional filter: title (case-insensitive substring match, e.g. 'Direktör', 'Ingenjör')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search board members of Swedish companies using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Wallenberg'."

        if research_context:
            logger.info("search_styrelse | context: %s", research_context)
        logger.info("search_styrelse called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = AktiebolagSearch(db)
            result = searcher.search_styrelse(
                keyword,
                limit=limit,
                offset=offset,
                titel=titel,
            )
            return format_styrelse_results(result)

        except Exception as exc:
            logger.error("search_styrelse failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Styrelse search failed \u2014 {exc!s}"

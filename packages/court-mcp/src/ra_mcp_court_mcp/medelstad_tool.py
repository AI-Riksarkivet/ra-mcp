"""MCP tool for searching Medelstad härad court records."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_court_lib import CourtSearch
from ra_mcp_court_lib.config import LANCEDB_URI

from .formatter import format_medelstad_results


logger = logging.getLogger("ra_mcp.court.medelstad_tool")

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


def register_medelstad_tool(mcp) -> None:
    """Register the search_medelstad MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_medelstad",
        tags={"court", "medelstad", "legal", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Medelstad härad court books 1668-1750 — 91,000 persons with 21,000 case summaries. "
            "Returns person name, title, parish, court date, case type, and full case summary text."
        ),
    )
    async def search_medelstad(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across Medelstad court records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        mal_typ: Annotated[
            str | None,
            Field(description="Optional filter: case type (case-insensitive substring match)."),
        ] = None,
        norm_forsamling: Annotated[
            str | None,
            Field(description="Optional filter: parish name (case-insensitive substring match)."),
        ] = None,
        datum_from: Annotated[
            str | None,
            Field(description="Optional filter: date range start inclusive (e.g. '1690-01-01'). String comparison on ting_dag field."),
        ] = None,
        datum_till: Annotated[
            str | None,
            Field(description="Optional filter: date range end inclusive (e.g. '1750-12-31'). String comparison on ting_dag field."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Medelstad härad court records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_medelstad | context: %s", research_context)
        logger.info("search_medelstad called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = CourtSearch(db)
            result = searcher.search_medelstad(
                keyword,
                limit=limit,
                offset=offset,
                mal_typ=mal_typ,
                norm_forsamling=norm_forsamling,
                datum_from=datum_from,
                datum_till=datum_till,
            )
            return format_medelstad_results(result)

        except Exception as exc:
            logger.error("search_medelstad failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Medelstad search failed \u2014 {exc!s}"

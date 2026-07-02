"""MCP tool for searching Fältjägare (Jämtland field regiment) soldier records."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated


if TYPE_CHECKING:
    import lancedb

from pydantic import Field

from ra_mcp_faltjagare_lib import FaltjagareSearch
from ra_mcp_faltjagare_lib.config import LANCEDB_URI

from .formatter import format_faltjagare_results


logger = logging.getLogger("ra_mcp.faltjagare.faltjagare_tool")

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


def register_faltjagare_tool(mcp) -> None:
    """Register the search_faltjagare MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_faltjagare",
        tags={"faltjagare", "soldier", "military", "regiment", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Jämtland field regiment records 1645-1901 — 43,000 soldier service records. "
            "Returns soldier name, family name, rank, company, parish, region, service period, "
            "and fate (killed/died/deserted)."
        ),
    )
    async def search_faltjagare(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across soldier records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        kompani: Annotated[
            str | None,
            Field(description="Optional filter: company name (case-insensitive substring match)."),
        ] = None,
        region: Annotated[
            str | None,
            Field(description="Optional filter: region (case-insensitive substring match, e.g. 'Jämtland', 'Härjedalen')."),
        ] = None,
        befattning: Annotated[
            str | None,
            Field(description="Optional filter: rank/position (case-insensitive substring match, e.g. 'Soldat', 'Korpral')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Jämtland field regiment soldier records using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_faltjagare | context: %s", research_context)
        logger.info("search_faltjagare called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = FaltjagareSearch(db)
            result = searcher.search(
                keyword,
                limit=limit,
                offset=offset,
                kompani=kompani,
                region=region,
                befattning=befattning,
            )
            return format_faltjagare_results(result)

        except Exception as exc:
            logger.error("search_faltjagare failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: Fältjägare search failed \u2014 {exc!s}"

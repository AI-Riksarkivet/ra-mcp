"""MCP tool for searching SDHK medieval charters."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_diplomatics_lib import DiplomaticsSearch
from ra_mcp_diplomatics_lib.config import LANCEDB_PATH

from .formatter import format_sdhk_results


logger = logging.getLogger("ra_mcp.diplomatics.sdhk_tool")

# Lazy-init LanceDB connection
_db = None


def _get_db():
    """Return a cached LanceDB connection, opening it on first use."""
    global _db
    if _db is None:
        import lancedb

        logger.info("Opening LanceDB at %s", LANCEDB_PATH)
        _db = lancedb.connect(str(LANCEDB_PATH))
    return _db


def register_sdhk_tool(mcp) -> None:
    """Register the search_sdhk MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_sdhk",
        tags={"diplomatics", "sdhk", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search SDHK (Diplomatarium Suecanum) — 44,000+ medieval Swedish charters dated before 1540. "
            "Returns charter metadata including title, author, date, place, language, summary, and edition excerpts. "
            "About 15,000 charters are digitized — these include IIIF manifest URLs you can pass to view_manifest. "
            "Results show digitization status: 'Digitized + Transcribed', 'Digitized', or 'Not digitized'. "
            "Only use view_manifest on results that have a manifest URL. "
            "Paginate with offset (0, 25, 50, ...)."
        ),
    )
    async def search_sdhk(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across SDHK charter text."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        author: Annotated[
            str | None,
            Field(description="Optional filter: only return charters with this author (case-insensitive substring match)."),
        ] = None,
        place: Annotated[
            str | None,
            Field(description="Optional filter: only return charters from this place (case-insensitive substring match)."),
        ] = None,
        language: Annotated[
            str | None,
            Field(description="Optional filter: only return charters in this language (case-insensitive substring match)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search SDHK medieval charter corpus using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Magnus'."

        if research_context:
            logger.info("search_sdhk | context: %s", research_context)
        logger.info("search_sdhk called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = DiplomaticsSearch(db)
            result = searcher.search_sdhk(
                keyword,
                limit=limit,
                offset=offset,
                author=author,
                place=place,
                language=language,
            )
            return format_sdhk_results(result)

        except Exception as exc:
            logger.error("search_sdhk failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: SDHK search failed — {exc!s}"

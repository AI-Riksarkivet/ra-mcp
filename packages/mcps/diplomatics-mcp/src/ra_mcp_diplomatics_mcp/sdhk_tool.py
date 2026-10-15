"""MCP tool for searching SDHK medieval charters."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_dataset_lib import get_lancedb, require_keyword
from ra_mcp_diplomatics_lib import DiplomaticsSearch
from ra_mcp_diplomatics_lib.config import LANCEDB_URI

from .formatter import format_sdhk_results


logger = logging.getLogger("ra_mcp.diplomatics.sdhk_tool")


def register_sdhk_tool(mcp: FastMCP) -> None:
    """Register the search_sdhk MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_sdhk",
        tags={"diplomatics", "sdhk", "search"},
        title="Search SDHK medieval charters",
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search SDHK (Diplomatarium Suecanum) — 44,000+ medieval Swedish charters dated before 1540. "
            "Returns results as a markdown table with key columns (ID, date, place, author, summary, status). "
            "ALWAYS present search results to the user as a table — do not convert to prose. "
            "About 15,000 charters are digitized — these include IIIF manifest URLs you can pass to view_manifest. "
            "Only use view_manifest on results that have a manifest URL. "
            "Paginate with offset (0, 25, 50, ...)."
        ),
    )
    def search_sdhk(
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
        if err := require_keyword(keyword, "'Magnus'"):
            return err

        if research_context:
            logger.info("search_sdhk | context: %s", research_context)
        logger.info("search_sdhk called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = get_lancedb(LANCEDB_URI)
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
            mark_span_error(f"SDHK search failed: {exc!s}")
            return f"Error: SDHK search failed — {exc!s}"

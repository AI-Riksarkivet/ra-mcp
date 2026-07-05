"""MCP tool for searching Videobutiker (video rental stores)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_dataset_lib import get_lancedb, require_keyword
from ra_mcp_specialsok_lib import SpecialsokSearch
from ra_mcp_specialsok_lib.config import LANCEDB_URI

from .formatter import format_video_results


logger = logging.getLogger("ra_mcp.specialsok.video_tool")


def register_video_tool(mcp: FastMCP) -> None:
    """Register the search_video MCP tool."""

    @mcp.tool(
        name="search_video",
        tags={"specialsok", "video", "stores", "retail", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=("Search Swedish video rental stores 1991-1994 — 7,000 stores across Sweden."),
    )
    def search_video(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across video store records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        laen: Annotated[
            str | None,
            Field(description="Optional filter: county name (case-insensitive substring match, e.g. 'Stockholm')."),
        ] = None,
        kommun: Annotated[
            str | None,
            Field(description="Optional filter: municipality name (case-insensitive substring match)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish video rental store records."""
        if err := require_keyword(keyword, "'Stockholm'"):
            return err

        if research_context:
            logger.info("search_video | context: %s", research_context)
        logger.info("search_video called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = get_lancedb(LANCEDB_URI)
            searcher = SpecialsokSearch(db)
            result = searcher.search_video(keyword, limit=limit, offset=offset, laen=laen, kommun=kommun)
            return format_video_results(result)
        except Exception as exc:
            logger.error("search_video failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            mark_span_error(f"Video search failed: {exc!s}")
            return f"Error: Video search failed \u2014 {exc!s}"

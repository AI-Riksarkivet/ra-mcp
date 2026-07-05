"""MCP tool for searching Presskonferenser (government press conferences)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_dataset_lib import get_lancedb, require_keyword
from ra_mcp_specialsok_lib import SpecialsokSearch
from ra_mcp_specialsok_lib.config import LANCEDB_URI

from .formatter import format_press_results


logger = logging.getLogger("ra_mcp.specialsok.press_tool")


def register_press_tool(mcp: FastMCP) -> None:
    """Register the search_press MCP tool."""

    @mcp.tool(
        name="search_press",
        tags={"specialsok", "press", "government", "media", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=("Search Swedish government press conferences 1993-2017 — 5,700 conferences with titles and content descriptions."),
    )
    def search_press(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across press conference records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        aar: Annotated[
            str | None,
            Field(description="Optional filter: year (case-insensitive substring match, e.g. '2005')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish government press conference records."""
        if err := require_keyword(keyword, "'EU'"):
            return err

        if research_context:
            logger.info("search_press | context: %s", research_context)
        logger.info("search_press called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = get_lancedb(LANCEDB_URI)
            searcher = SpecialsokSearch(db)
            result = searcher.search_press(keyword, limit=limit, offset=offset, aar=aar)
            return format_press_results(result)
        except Exception as exc:
            logger.error("search_press failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            mark_span_error(f"Press search failed: {exc!s}")
            return f"Error: Press search failed \u2014 {exc!s}"

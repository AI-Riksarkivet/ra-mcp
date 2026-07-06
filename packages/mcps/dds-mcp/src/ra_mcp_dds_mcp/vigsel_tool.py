"""MCP tool for searching Swedish marriage records (Vigsel)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_dataset_lib import get_lancedb, require_keyword, require_ordered_range
from ra_mcp_dds_lib import DDSSearch
from ra_mcp_dds_lib.config import LANCEDB_URI

from .formatter import format_vigsel_results


logger = logging.getLogger("ra_mcp.dds.vigsel_tool")


def register_vigsel_tool(mcp: FastMCP) -> None:
    """Register the search_vigsel MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_vigsel",
        tags={"dds", "church", "marriage", "genealogy", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Swedish marriage records — 447,000 records from 1600s-1929. "
            "Returns bride and groom names, occupations, ages, civil status, "
            "home parishes, and banns dates."
        ),
    )
    def search_vigsel(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across marriage records."),
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
        datum_from: Annotated[
            str | None,
            Field(description="Optional filter: earliest date (YYYY-MM-DD format, inclusive)."),
        ] = None,
        datum_till: Annotated[
            str | None,
            Field(description="Optional filter: latest date (YYYY-MM-DD format, inclusive)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish marriage records using full-text search."""
        if err := require_keyword(keyword, "'Andersson'"):
            return err
        if err := require_ordered_range(datum_from, datum_till, "date"):
            return err

        if research_context:
            logger.info("search_vigsel | context: %s", research_context)
        logger.info("search_vigsel called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = get_lancedb(LANCEDB_URI)
            searcher = DDSSearch(db)
            result = searcher.search_vigsel(
                keyword,
                limit=limit,
                offset=offset,
                forsamling=forsamling,
                lan=lan,
                datum_from=datum_from,
                datum_till=datum_till,
            )
            return format_vigsel_results(result)

        except Exception as exc:
            logger.error("search_vigsel failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            mark_span_error(f"Vigsel search failed \u2014 {exc!s}")
            return f"Error: Vigsel search failed \u2014 {exc!s}"

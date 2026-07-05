"""MCP tool for searching Rösträtt (women's suffrage petition 1913-1914)."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_dataset_lib import get_lancedb
from ra_mcp_suffrage_lib import SuffrageSearch
from ra_mcp_suffrage_lib.config import LANCEDB_URI

from .formatter import format_rostratt_results


logger = logging.getLogger("ra_mcp.suffrage.rostratt_tool")


def register_rostratt_tool(mcp) -> None:
    """Register the search_rostratt MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_rostratt",
        tags={"suffrage", "rostratt", "petition", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search women's suffrage petition signatures 1913-1914 — 29,000 names from 5 counties. "
            "Returns signer name, title, occupation, address, town, county, and monetary contributions."
        ),
    )
    def search_rostratt(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across Rösträtt petition records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        lan: Annotated[
            str | None,
            Field(description="Optional filter: county name (case-insensitive substring match, e.g. 'Blekinge', 'Gotland')."),
        ] = None,
        ortens_namn: Annotated[
            str | None,
            Field(description="Optional filter: town name (case-insensitive substring match)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Rösträtt women's suffrage petition records using full-text search."""
        if not keyword or not keyword.strip():
            mark_span_error("keyword must not be empty", error_type="validation")
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Andersson'."

        if research_context:
            logger.info("search_rostratt | context: %s", research_context)
        logger.info("search_rostratt called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = get_lancedb(LANCEDB_URI)
            searcher = SuffrageSearch(db)
            result = searcher.search_rostratt(
                keyword,
                limit=limit,
                offset=offset,
                lan=lan,
                ortens_namn=ortens_namn,
            )
            return format_rostratt_results(result)

        except Exception as exc:
            logger.error("search_rostratt failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            mark_span_error(f"Rösträtt search failed \u2014 {exc!s}")
            return f"Error: Rösträtt search failed \u2014 {exc!s}"

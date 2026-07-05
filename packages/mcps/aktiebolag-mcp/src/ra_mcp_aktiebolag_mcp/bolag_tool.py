"""MCP tool for searching Aktiebolag (Swedish joint-stock companies)."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_aktiebolag_lib import AktiebolagSearch
from ra_mcp_aktiebolag_lib.config import LANCEDB_URI
from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_dataset_lib import get_lancedb

from .formatter import format_bolag_results


logger = logging.getLogger("ra_mcp.aktiebolag.bolag_tool")


def register_bolag_tool(mcp) -> None:
    """Register the search_bolag MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_bolag",
        tags={"aktiebolag", "company", "business", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Swedish joint-stock companies 1901-1935 — 12,500 companies with >100,000 kr capital. "
            "Returns company name, purpose, address, board seat city, managing director, share capital, "
            "and board member names."
        ),
    )
    def search_bolag(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across company records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        styrelsesate: Annotated[
            str | None,
            Field(description="Optional filter: board seat city (case-insensitive substring match, e.g. 'Stockholm', 'Göteborg')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish joint-stock company records using full-text search."""
        if not keyword or not keyword.strip():
            mark_span_error("keyword must not be empty", error_type="validation")
            return "Error: keyword must not be empty. Provide a search term, e.g. 'Separator'."

        if research_context:
            logger.info("search_bolag | context: %s", research_context)
        logger.info("search_bolag called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = get_lancedb(LANCEDB_URI)
            searcher = AktiebolagSearch(db)
            result = searcher.search_bolag(
                keyword,
                limit=limit,
                offset=offset,
                styrelsesate=styrelsesate,
            )
            return format_bolag_results(result)

        except Exception as exc:
            logger.error("search_bolag failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            mark_span_error(f"Bolag search failed \u2014 {exc!s}")
            return f"Error: Bolag search failed \u2014 {exc!s}"

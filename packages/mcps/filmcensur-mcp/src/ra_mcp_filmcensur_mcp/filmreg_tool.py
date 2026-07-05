"""MCP tool for searching Filmcensur (Swedish film censorship) records."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_dataset_lib import get_lancedb, require_keyword
from ra_mcp_filmcensur_lib import FilmcensurSearch
from ra_mcp_filmcensur_lib.config import LANCEDB_URI

from .formatter import format_filmreg_results


logger = logging.getLogger("ra_mcp.filmcensur.filmreg_tool")


def register_filmreg_tool(mcp) -> None:
    """Register the search_filmreg MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_filmreg",
        tags={"filmcensur", "film", "censorship", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Swedish film censorship records — 60,000 films reviewed 1911-2011. "
            "Returns original and Swedish titles, production year/country, category, age rating, "
            "number of cuts, producer, free-text descriptions, and notes."
        ),
    )
    def search_filmreg(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across film censorship records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        filmkategori: Annotated[
            str | None,
            Field(description="Optional filter: film category (case-insensitive substring match, e.g. 'Spelfilm', 'Dokumentär')."),
        ] = None,
        produktionsland: Annotated[
            str | None,
            Field(description="Optional filter: production country (case-insensitive substring match, e.g. 'Sverige', 'USA')."),
        ] = None,
        aaldersgraens: Annotated[
            str | None,
            Field(description="Optional filter: age rating (case-insensitive substring match, e.g. '15 år', 'Barntillåten')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Swedish film censorship records using full-text search."""
        if err := require_keyword(keyword, "'Bergman'"):
            return err

        if research_context:
            logger.info("search_filmreg | context: %s", research_context)
        logger.info("search_filmreg called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = get_lancedb(LANCEDB_URI)
            searcher = FilmcensurSearch(db)
            result = searcher.search_filmreg(
                keyword,
                limit=limit,
                offset=offset,
                filmkategori=filmkategori,
                produktionsland=produktionsland,
                aaldersgraens=aaldersgraens,
            )
            return format_filmreg_results(result)

        except Exception as exc:
            logger.error("search_filmreg failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            msg = f"Error: Filmreg search failed \u2014 {exc!s}"
            mark_span_error(msg)
            return msg

"""MCP tool for searching Kurhuset (venereal disease hospital patients)."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_dataset_lib import get_lancedb, require_keyword
from ra_mcp_specialsok_lib import SpecialsokSearch
from ra_mcp_specialsok_lib.config import LANCEDB_URI

from .formatter import format_kurhuset_results


logger = logging.getLogger("ra_mcp.specialsok.kurhuset_tool")


def register_kurhuset_tool(mcp) -> None:
    """Register the search_kurhuset MCP tool."""

    @mcp.tool(
        name="search_kurhuset",
        tags={"specialsok", "kurhuset", "hospital", "medical", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=("Search hospital patient records 1817-1866 — 3,000 patients with diagnoses, treatments, and outcomes."),
    )
    def search_kurhuset(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across hospital patient records."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        sjukdom: Annotated[
            str | None,
            Field(description="Optional filter: disease name (case-insensitive substring match, e.g. 'syfilis')."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search Kurhuset hospital patient records."""
        if err := require_keyword(keyword, "'syfilis'"):
            return err

        if research_context:
            logger.info("search_kurhuset | context: %s", research_context)
        logger.info("search_kurhuset called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = get_lancedb(LANCEDB_URI)
            searcher = SpecialsokSearch(db)
            result = searcher.search_kurhuset(keyword, limit=limit, offset=offset, sjukdom=sjukdom)
            return format_kurhuset_results(result)
        except Exception as exc:
            logger.error("search_kurhuset failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            mark_span_error(f"Kurhuset search failed: {exc!s}")
            return f"Error: Kurhuset search failed \u2014 {exc!s}"

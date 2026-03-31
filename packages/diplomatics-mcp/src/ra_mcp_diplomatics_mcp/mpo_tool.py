"""MCP tool for searching MPO medieval parchment fragments."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_diplomatics_lib import DiplomaticsSearch
from ra_mcp_diplomatics_lib.config import LANCEDB_URI

from .formatter import format_mpo_results


logger = logging.getLogger("ra_mcp.diplomatics.mpo_tool")

# Lazy-init LanceDB connection
_db = None


def _get_db():
    """Return a cached LanceDB connection, opening it on first use."""
    global _db
    if _db is None:
        import lancedb

        logger.info("Opening LanceDB at %s", LANCEDB_URI)
        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_mpo_tool(mcp) -> None:
    """Register the search_mpo MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_mpo",
        tags={"diplomatics", "mpo", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search MPO (Medeltida Pergamentomslag) — 23,000+ medieval parchment fragments used as bookbinding covers. "
            "Returns fragment metadata including manuscript type, category, title, author, dating, origin, collection, "
            "institution, script, material, and content descriptions. "
            "Each result includes a IIIF manifest URL for viewing fragment images — pass this to view_manifest. "
            "Paginate with offset (0, 25, 50, ...)."
        ),
    )
    async def search_mpo(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across MPO fragment text."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        category: Annotated[
            str | None,
            Field(description="Optional filter: only return fragments in this category (case-insensitive substring match)."),
        ] = None,
        institution: Annotated[
            str | None,
            Field(description="Optional filter: only return fragments held at this institution (case-insensitive substring match)."),
        ] = None,
        script: Annotated[
            str | None,
            Field(description="Optional filter: only return fragments with this script type (case-insensitive substring match)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search MPO medieval parchment fragment corpus using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'liturgy'."

        if research_context:
            logger.info("search_mpo | context: %s", research_context)
        logger.info("search_mpo called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = DiplomaticsSearch(db)
            result = searcher.search_mpo(
                keyword,
                limit=limit,
                offset=offset,
                category=category,
                institution=institution,
                script=script,
            )
            return format_mpo_results(result)

        except Exception as exc:
            logger.error("search_mpo failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: MPO search failed — {exc!s}"

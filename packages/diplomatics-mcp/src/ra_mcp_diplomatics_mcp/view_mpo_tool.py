"""MCP tool for viewing a single MPO parchment fragment in the document viewer."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import uuid4

from fastmcp import Context
from fastmcp.server.apps import UI_EXTENSION_ID, AppConfig
from fastmcp.tools import ToolResult
from mcp import types
from pydantic import Field

from ra_mcp_diplomatics_lib import DiplomaticsSearch
from ra_mcp_diplomatics_lib.config import LANCEDB_URI
from ra_mcp_viewer_mcp.formatter import build_summary, error_result
from ra_mcp_viewer_mcp.models import ViewerState
from ra_mcp_viewer_mcp.resolve import manifest_resolve_document
from ra_mcp_viewer_mcp.state import put_state
from ra_mcp_viewer_mcp.tools import RESOURCE_URI

from .formatter import format_mpo_info


logger = logging.getLogger("ra_mcp.diplomatics.view_mpo")

_db = None


def _get_db():
    global _db
    if _db is None:
        import lancedb

        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_view_mpo_tool(mcp) -> None:
    """Register the view_mpo MCP tool."""

    @mcp.tool(
        name="view_mpo",
        tags={"diplomatics", "mpo", "viewer"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "View an MPO parchment fragment in the document viewer with full codicological metadata. "
            "Takes an MPO ID (from search_mpo results) and opens the interactive viewer "
            "with the fragment images and a metadata panel showing manuscript type, dating, "
            "script, material, content, decoration, and damage descriptions."
        ),
        app=AppConfig(resource_uri=RESOURCE_URI),
    )
    async def view_mpo(
        mpo_id: Annotated[int, Field(description="MPO fragment ID (e.g. 1, 42).")],
        ctx: Context,
        highlight_term: Annotated[str | None, Field(description="Optional search term to highlight.")] = None,
        max_pages: Annotated[int, Field(description="Maximum pages to load.", le=20)] = 20,
    ) -> ToolResult:
        """Look up MPO record and open in viewer with full metadata."""
        try:
            db = _get_db()
            searcher = DiplomaticsSearch(db)
            row = searcher.get_mpo_by_id(mpo_id)
        except Exception as exc:
            logger.error("view_mpo: DB lookup failed: %s", exc, exc_info=True)
            return error_result(f"Error looking up MPO {mpo_id}: {exc}")

        if row is None:
            return error_result(f"MPO {mpo_id} not found.")

        manifest_url = row.get("manifest_url", "")
        if not manifest_url:
            return error_result(
                f"MPO {mpo_id} has no IIIF manifest — no images available. "
                f"The record metadata is:\n\n{format_mpo_info(row)}"
            )

        try:
            resolved = await manifest_resolve_document(manifest_url, max_pages)
        except (ValueError, LookupError) as exc:
            return error_result(str(exc))
        except Exception as exc:
            logger.error("view_mpo: manifest resolution failed: %s", exc, exc_info=True)
            return error_result(f"Error resolving manifest: {exc}")

        document_info = format_mpo_info(row)

        has_ui = ctx.client_supports_extension(UI_EXTENSION_ID)
        summary = build_summary(
            len(resolved.image_urls),
            resolved.page_numbers,
            has_ui,
            resolved.image_urls,
        )

        view_id = str(uuid4())
        state = ViewerState(
            view_id=view_id,
            image_urls=resolved.image_urls,
            text_layer_urls=resolved.text_layer_urls,
            page_numbers=resolved.page_numbers,
            document_info=document_info,
            highlight_term=highlight_term or "",
            reference_code=f"MPO {mpo_id}",
        )
        sc = await put_state(state)

        logger.info("view_mpo: MPO %d, %d page(s), view_id=%s", mpo_id, len(resolved.image_urls), view_id)
        return ToolResult(
            content=[types.TextContent(type="text", text=summary)],
            structured_content=sc,
        )

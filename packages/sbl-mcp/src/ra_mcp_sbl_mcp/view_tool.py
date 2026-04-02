"""MCP tools for viewing SBL biographical articles in a rich UI.

Provides three tools:
- view_sbl_article: model+app visible, creates the iframe
- load_sbl_article: app-only, for in-place article loading (cross-references)
- get_sbl_state: app-only, polling endpoint for LLM-initiated loads
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastmcp.server.apps import AppConfig, ResourceCSP
from fastmcp.tools import ToolResult
from mcp import types
from pydantic import Field

from ra_mcp_sbl_lib.config import SBL_TABLE

from . import state
from .sbl_tool import _get_db


logger = logging.getLogger("ra_mcp.sbl.view_tool")

DIST_DIR = Path(__file__).parent / "dist"
RESOURCE_URI = "ui://sbl-article-viewer/mcp-app.html"


def _fetch_article(article_id: int) -> dict | None:
    """Fetch an SBL article by ID from LanceDB. Returns the row dict or None."""
    db = _get_db()
    table = db.open_table(SBL_TABLE)
    rows = table.search().where(f"article_id = {article_id}").limit(1).to_list()
    return rows[0] if rows else None


def _article_summary(rec: dict) -> str:
    """Build a short text summary for an article record."""
    surname = rec.get("surname", "")
    given_name = rec.get("given_name", "")
    name = f"{given_name} {surname}".strip() if given_name else surname
    occupation = rec.get("occupation", "")
    summary = f"SBL article: {name}"
    if occupation:
        summary += f" — {occupation}"
    return summary


def register_view_tool(mcp) -> None:
    """Register the view/load/state tools and UI resource."""

    @mcp.resource(
        uri=RESOURCE_URI,
        app=AppConfig(
            csp=ResourceCSP(
                resource_domains=["https://sok.riksarkivet.se"],
            ),
        ),
    )
    def get_ui_resource() -> str:
        html_path = DIST_DIR / "mcp-app.html"
        if not html_path.exists():
            msg = f"UI resource not found: {html_path}. Run 'npm run build' in packages/sbl-mcp/"
            raise FileNotFoundError(msg)
        return html_path.read_text(encoding="utf-8")

    # --- Tool 1: view_sbl_article (model + app visible, creates iframe) ---

    @mcp.tool(
        name="view_sbl_article",
        tags={"sbl", "biography", "viewer"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        app=AppConfig(resource_uri=RESOURCE_URI),
        description=(
            "Display an SBL biographical article in a rich viewer. "
            "Takes an article_id from search_sbl results and shows the full article with portrait, "
            "career details, printed works, sources, and a link to the full biography on the SBL website. "
            "Use this after search_sbl to view a specific person's article."
        ),
    )
    async def view_sbl_article(
        article_id: Annotated[
            int,
            Field(description="The SBL article ID from search_sbl results."),
        ],
    ) -> ToolResult:
        """Display an SBL article in the viewer."""
        logger.info("view_sbl_article called with article_id=%d", article_id)

        try:
            rec = _fetch_article(article_id)
            if not rec:
                return ToolResult(
                    content=[types.TextContent(type="text", text=f"No SBL article found with id {article_id}.")],
                )

            state.set_article(rec)

            return ToolResult(
                content=[types.TextContent(type="text", text=_article_summary(rec))],
                structured_content=rec,
            )

        except Exception as exc:
            logger.error("view_sbl_article failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return ToolResult(
                content=[types.TextContent(type="text", text=f"Error: Failed to load SBL article — {exc!s}")],
            )

    # --- Tool 2: load_sbl_article (app-only, for cross-reference navigation) ---

    @mcp.tool(
        name="load_sbl_article",
        tags={"sbl", "biography", "viewer"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
        description="Load an SBL article into the viewer (app-only, for cross-reference navigation).",
    )
    async def load_sbl_article(
        article_id: Annotated[
            int,
            Field(description="The SBL article ID to load."),
        ],
    ) -> ToolResult:
        """Load an article in-place (called by the UI on cross-reference clicks)."""
        logger.info("load_sbl_article called with article_id=%d", article_id)

        try:
            rec = _fetch_article(article_id)
            if not rec:
                return ToolResult(
                    content=[types.TextContent(type="text", text=f"No SBL article found with id {article_id}.")],
                )

            state.set_article(rec)

            return ToolResult(
                content=[types.TextContent(type="text", text=_article_summary(rec))],
                structured_content=rec,
            )

        except Exception as exc:
            logger.error("load_sbl_article failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return ToolResult(
                content=[types.TextContent(type="text", text=f"Error: Failed to load SBL article — {exc!s}")],
            )

    # --- Tool 3: get_sbl_state (app-only, polling for LLM-initiated loads) ---

    @mcp.tool(
        name="get_sbl_state",
        tags={"sbl", "biography", "viewer"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]),
        description="Get the current SBL article state (app-only, for polling).",
    )
    async def get_sbl_state() -> ToolResult:
        """Return the current article for the UI to poll."""
        rec = state.get_article()
        if not rec:
            return ToolResult(
                content=[types.TextContent(type="text", text="No article loaded.")],
            )

        return ToolResult(
            content=[types.TextContent(type="text", text=_article_summary(rec))],
            structured_content=rec,
        )

"""MCP tool for viewing SBL biographical articles in a rich UI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastmcp.server.apps import AppConfig, ResourceCSP
from fastmcp.tools import ToolResult
from mcp import types
from pydantic import Field

from ra_mcp_sbl_lib.config import SBL_TABLE

from .sbl_tool import _get_db


logger = logging.getLogger("ra_mcp.sbl.view_tool")

DIST_DIR = Path(__file__).parent / "dist"
RESOURCE_URI = "ui://sbl-article-viewer/mcp-app.html"


def register_view_tool(mcp) -> None:
    """Register the view_sbl_article tool and UI resource."""

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
            db = _get_db()
            table = db.open_table(SBL_TABLE)

            # Fetch the specific record by article_id
            rows = table.search().where(f"article_id = {article_id}").limit(1).to_list()

            if not rows:
                return ToolResult(
                    content=[types.TextContent(type="text", text=f"No SBL article found with id {article_id}.")],
                )

            rec = rows[0]
            surname = rec.get("surname", "")
            given_name = rec.get("given_name", "")
            name = f"{given_name} {surname}".strip() if given_name else surname
            occupation = rec.get("occupation", "")

            summary = f"SBL article: {name}"
            if occupation:
                summary += f" — {occupation}"

            return ToolResult(
                content=[types.TextContent(type="text", text=summary)],
                structured_content=rec,
            )

        except Exception as exc:
            logger.error("view_sbl_article failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return ToolResult(
                content=[types.TextContent(type="text", text=f"Error: Failed to load SBL article — {exc!s}")],
            )

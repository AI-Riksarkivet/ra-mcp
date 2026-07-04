"""FastMCP server definition for SBL biographical search and viewer tools."""

from fastmcp import FastMCP

from .sbl_tool import register_sbl_tool
from .view_tool import register_view_tool


sbl_mcp = FastMCP(
    name="ra-sbl-mcp",
    instructions=(
        "Search Svenskt biografiskt lexikon (SBL) — 9,400+ biographical articles about notable "
        "Swedish individuals from medieval times to the 20th century. "
        "Filter by gender, occupation, place, or year range. "
        "Use view_sbl_article to display a specific article with portrait and full details."
    ),
)

register_sbl_tool(sbl_mcp)
register_view_tool(sbl_mcp)

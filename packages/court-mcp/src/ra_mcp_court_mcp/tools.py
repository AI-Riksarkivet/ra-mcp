"""FastMCP server definition for court records search tools."""

from fastmcp import FastMCP

from .domboksregister_tool import register_domboksregister_tool
from .medelstad_tool import register_medelstad_tool


court_mcp = FastMCP(
    name="ra-court-mcp",
    instructions=(
        "Search Swedish court records — Domboksregister (Västra härad 1611-1730, 88K persons) "
        "and Medelstad härad (1668-1750, 91K persons with 21K case summaries). "
        "Use search_domboksregister for Västra härad court cases with role and parish filters. "
        "Use search_medelstad for Medelstad court cases with case type and parish filters."
    ),
)

register_domboksregister_tool(court_mcp)
register_medelstad_tool(court_mcp)

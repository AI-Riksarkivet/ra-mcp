"""FastMCP server definition for women's suffrage records search tools."""

from fastmcp import FastMCP

from .fkpr_tool import register_fkpr_tool
from .rostratt_tool import register_rostratt_tool


suffrage_mcp = FastMCP(
    name="ra-suffrage-mcp",
    instructions=(
        "Search Swedish women's suffrage records — petition signatures and association members. "
        "Use search_rostratt for the 1913-1914 suffrage petition (29,000 names from 5 counties). "
        "Use search_fkpr for the Gothenburg FKPR suffrage association members 1911-1920 (1,700 women)."
    ),
)

register_rostratt_tool(suffrage_mcp)
register_fkpr_tool(suffrage_mcp)

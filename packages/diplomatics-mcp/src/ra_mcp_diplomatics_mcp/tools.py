"""FastMCP server definition for diplomatics search tools."""

from fastmcp import FastMCP

from .sdhk_tool import register_sdhk_tool
from .mpo_tool import register_mpo_tool


diplomatics_mcp = FastMCP(
    name="ra-diplomatics-mcp",
    instructions=(
        "Search medieval Swedish documents: SDHK (44,000+ medieval charters before 1540) "
        "and MPO (23,000+ medieval parchment fragments). "
        "Both return IIIF manifest URLs — use view_manifest to view document images."
    ),
)

register_sdhk_tool(diplomatics_mcp)
register_mpo_tool(diplomatics_mcp)

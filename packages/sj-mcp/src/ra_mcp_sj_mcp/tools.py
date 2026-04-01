"""FastMCP server definition for SJ railway records search tools."""

from fastmcp import FastMCP

from .juda_tool import register_juda_tool
from .ritningar_tool import register_ritningar_tool


sj_mcp = FastMCP(
    name="ra-sj-mcp",
    instructions=(
        "Search Swedish State Railways (SJ) records — JUDA property register (198K properties) "
        "and FIRA/SIRA technical drawings (118K drawings of stations, buildings, and infrastructure). "
        "Use search_juda for railway properties with owner filter. "
        "Use search_ritningar for technical drawings with district filter."
    ),
)

register_juda_tool(sj_mcp)
register_ritningar_tool(sj_mcp)

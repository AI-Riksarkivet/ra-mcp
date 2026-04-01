"""FastMCP server definition for DDS church records search tools."""

from fastmcp import FastMCP

from .doda_tool import register_doda_tool
from .fodelse_tool import register_fodelse_tool
from .vigsel_tool import register_vigsel_tool


dds_mcp = FastMCP(
    name="ra-dds-mcp",
    instructions=(
        "Search Swedish church records (DDS) — births, deaths, and marriages from the 1600s to early 1900s "
        "across multiple Swedish counties. Over 2.5 million records for genealogical research."
    ),
)

register_fodelse_tool(dds_mcp)
register_doda_tool(dds_mcp)
register_vigsel_tool(dds_mcp)

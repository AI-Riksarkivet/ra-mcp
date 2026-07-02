"""FastMCP server definition for Fältjägare soldier record search tools."""

from fastmcp import FastMCP

from .faltjagare_tool import register_faltjagare_tool


faltjagare_mcp = FastMCP(
    name="ra-faltjagare-mcp",
    instructions=(
        "Search Jämtland field regiment soldier records (Fältjägare) 1645-1901 — 43,000 service records. "
        "Returns soldier name, family name, rank, company, parish, region, service period, birth details, "
        "and fate (killed in action, place of death). "
        "Filter by company, region, or rank."
    ),
)

register_faltjagare_tool(faltjagare_mcp)

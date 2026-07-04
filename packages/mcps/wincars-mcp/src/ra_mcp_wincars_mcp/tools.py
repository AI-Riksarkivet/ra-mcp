"""FastMCP server definition for Wincars vehicle registration search tools."""

from fastmcp import FastMCP

from .wincars_tool import register_wincars_tool


wincars_mcp = FastMCP(
    name="ra-wincars-mcp",
    instructions=(
        "Search Norrland vehicle registration records (Wincars) — 1.5 million vehicles registered "
        "across 5 northern Swedish counties (Gävleborg, Jämtland, Norrbotten, Västerbotten, Västernorrland) "
        "1916-1972. Returns registration numbers, vehicle type, make/model, year, chassis/engine numbers, "
        "registration/deregistration dates, domicile, and status (active/written off/scrapped). "
        "Filter by vehicle type, domicile, or make."
    ),
)

register_wincars_tool(wincars_mcp)

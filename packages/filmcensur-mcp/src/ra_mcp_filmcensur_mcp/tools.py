"""FastMCP server definition for Filmcensur film censorship search tools."""

from fastmcp import FastMCP

from .filmreg_tool import register_filmreg_tool


filmcensur_mcp = FastMCP(
    name="ra-filmcensur-mcp",
    instructions=(
        "Search Swedish film censorship records (Filmcensur) — 60,000 films reviewed by Statens biografbyrå "
        "1911-2011. Returns original and Swedish titles, production year/country, category, age rating, "
        "number of cuts, producer, free-text descriptions, and censor notes. "
        "Filter by film category, production country, or age rating."
    ),
)

register_filmreg_tool(filmcensur_mcp)

"""FastMCP server definition for Rosenberg geographical lexicon search tools."""

from fastmcp import FastMCP

from .rosenberg_tool import register_rosenberg_tool


rosenberg_mcp = FastMCP(
    name="ra-rosenberg-mcp",
    instructions=(
        "Search Rosenberg's geographical lexicon of Sweden (Geografiskt-statistiskt handlexikon öfver Sverige) — "
        "66,000 historical places with descriptions, parish, hundred, county, and industry/feature flags. "
        "Use for looking up historical Swedish places, parishes, and their descriptions."
    ),
)

register_rosenberg_tool(rosenberg_mcp)

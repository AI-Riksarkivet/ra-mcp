"""FastMCP server definition for TORA geocoding tools."""

from fastmcp import FastMCP

from .tora_tool import register_tora_tool


tora_mcp = FastMCP(
    name="ra-tora-mcp",
    instructions=(
        "Geocode historical Swedish places using TORA (Topografiskt register på Riksarkivet). "
        "51,000 settlements with WGS84 coordinates, linked to parishes, municipalities, and counties. "
        "Use for looking up coordinates and administrative context of historical Swedish places."
    ),
)

register_tora_tool(tora_mcp)

"""FastMCP server definition for Specialsök search tools."""

from fastmcp import FastMCP

from .fangrullor_tool import register_fangrullor_tool
from .flygvapen_tool import register_flygvapen_tool
from .kurhuset_tool import register_kurhuset_tool
from .press_tool import register_press_tool
from .video_tool import register_video_tool


specialsok_mcp = FastMCP(
    name="ra-specialsok-mcp",
    instructions=(
        "Search five Swedish historical datasets from Riksarkivet Specialsök: "
        "Flygvapenhaverier (2,400 military aviation accidents 1912-2007), "
        "Fångrullor (11,500 Östersund prison records 1810-1900), "
        "Kurhuset (3,000 venereal disease hospital patients 1817-1866), "
        "Presskonferenser (5,700 government press conferences 1993-2017), "
        "Videobutiker (7,000 video rental stores 1991-1994). "
        "Each dataset has its own search tool with dataset-specific filters."
    ),
)

register_flygvapen_tool(specialsok_mcp)
register_fangrullor_tool(specialsok_mcp)
register_kurhuset_tool(specialsok_mcp)
register_press_tool(specialsok_mcp)
register_video_tool(specialsok_mcp)

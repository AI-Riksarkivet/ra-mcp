"""
Riksarkivet Browse MCP Server.

This module sets up the FastMCP server and registers browse tools
for viewing full document pages.
"""

from fastmcp import FastMCP

from .browse_tool import register_browse_tool


browse_mcp = FastMCP(
    name="ra-browse-mcp",
    instructions="""
    Riksarkivet (RA) Browse MCP Server — view full document page transcriptions from the Swedish National Archives.

    TOOL:
    - browse_document: View full page transcriptions by reference code (single pages, ranges, or lists)

    SESSION MEMORY:
    This tool tracks which pages it has shown you. Re-browsing the same pages returns stubs.
    Prefer referencing page transcriptions already in context. Pass dedup=False to force full text.
    """,
)


# Register browse tool
register_browse_tool(browse_mcp)

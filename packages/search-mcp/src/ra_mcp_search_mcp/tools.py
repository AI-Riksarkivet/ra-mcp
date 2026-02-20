"""
Riksarkivet Search MCP Server.

This module sets up the FastMCP server and registers search tools
for searching transcribed historical documents.
"""

from fastmcp import FastMCP

from .search_tool import register_search_tool


search_mcp = FastMCP(
    name="ra-search-mcp",
    instructions="""
    Riksarkivet (RA) Search MCP Server — search access to historical documents from the Swedish National Archives.

    TOOLS:
    - search_transcribed: Search AI-transcribed text in digitised documents (full-text, snippets, page links)
    - search_metadata: Search document metadata — titles, names, places, descriptions (2M+ records with only_digitised=False)

    SESSION MEMORY:
    These tools track what they have shown you in this session. Re-calling the same search returns compact stubs
    for already-seen documents. Prefer referencing data already in your conversation context. Pass dedup=False
    to force full results repeated.
    """,
)


# Register search tool
register_search_tool(search_mcp)

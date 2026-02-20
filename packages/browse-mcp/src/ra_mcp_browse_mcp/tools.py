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
    🏛️ Riksarkivet (RA) Browse MCP Server

    This server provides access to full document page transcriptions from the Swedish National Archives.

    AVAILABLE TOOL:

    📖 browse_document - View full page transcriptions by reference code
       - Returns complete transcribed text from document pages
       - Supports single pages, page ranges, or comma-separated page lists
       - Provides links to original images and ALTO XML
       - Optional search term highlighting

    BROWSE STRATEGY:
    1. Use reference codes and page numbers from search results
    2. Request specific pages or ranges (e.g., "5" or "1-10" or "5,7,9")
    3. Review full transcriptions in their original language
    4. Follow links to bildvisaren to view original document images

    TYPICAL WORKFLOW:
    1. First, use search tools (separate server) to find relevant documents
    2. Note the reference codes and page numbers from search results
    3. Use browse_document() to retrieve full transcriptions
    4. Examine context around interesting passages

    SESSION MEMORY & AVOIDING REDUNDANT CALLS:
    - This tool tracks which pages it has shown you in this session. Re-browsing the same pages returns one-liner stubs instead of full transcriptions, saving tokens.
    - PREFER referencing page transcriptions already in your conversation context over re-calling this tool. If you already have the text of a page, use it directly.
    - Only call browse_document again when you need pages you haven't seen yet.
    - Pass dedup=False if you truly need full transcriptions repeated.

    All tools return rich, formatted text optimized for LLM understanding.
    """,
)


# Register browse tool
register_browse_tool(browse_mcp)

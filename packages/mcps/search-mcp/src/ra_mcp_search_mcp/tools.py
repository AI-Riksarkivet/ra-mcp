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

    TRANSCRIPTION QUALITY:
    All transcriptions are AI-generated using HTR (Handwritten Text Recognition) and OCR models.
    They contain recognition errors — misread characters, merged/split words, and garbled passages are common,
    especially in older or damaged documents. ALWAYS use fuzzy search (~) to compensate for these errors
    and significantly increase the number of hits. For example, use stockholm~1 instead of Stockholm.

    TOOLS:
    - search_transcribed: Search AI-transcribed text in digitised documents (full-text, snippets, page links)
    - search_metadata: Search document metadata — titles, names, places, descriptions (2M+ records with only_digitised=False)
      When using name or place parameters, set only_digitised=False — most person/place catalog entries lack digitised images.

    SESSION MEMORY:
    These tools track what they have shown you in this session. Re-calling the same search returns compact stubs
    for already-seen documents. Prefer referencing data already in your conversation context. Pass dedup=False
    to force full results repeated.
    """,
)


# Register search tool
register_search_tool(search_mcp)

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
    🏛️ Riksarkivet (RA) Search MCP Server

    This server provides search access to transcribed historical documents from the Swedish National Archives.

    AVAILABLE TOOL:

    🔍 search_transcribed - Search for keywords in transcribed materials
       - Returns documents and pages containing the keyword (a subset of what is written on the document)
       - Offset parameter required to encourage comprehensive discovery
       - Provides direct links to images and ALTO XML
       - Supports advanced Solr search syntax (see SEARCH SYNTAX below)

    SEARCH STRATEGY FOR MAXIMUM DISCOVERY:
    1. Start with search_transcribed(keyword, offset=0) for initial hits (use syntax guide below when searching)
    2. Continue pagination with increasing offsets (50, 100, 150...) to find all matches
    3. EXPLORE RELATED TERMS: Search for similar/related words to gather comprehensive context
       - Historical variants and spellings (e.g., "trolldom" + "häxa" + "trollkona")
       - Synonyms and related concepts (e.g., "satan" + "djävul" for devil-related terms)
       - Different word forms (e.g., "trolleri" + "trollkonst" for witchcraft variants)
       - Period-appropriate terminology and archaic spellings
    4. Note reference codes and page numbers from results for detailed browsing with browse tools

    SEARCH SYNTAX (Solr Query Syntax):

    Basic Search:
    - "Stockholm" - Exact term search
    - "Stock*" - Wildcard (multiple characters)
    - "St?ckholm" - Wildcard (single character)

    Fuzzy & Proximity:
    - "Stockholm~" - Fuzzy search (edit distance 2)
    - "Stockholm~1" - Fuzzy with custom edit distance
    - '\"Stockholm trolldom\"~10' - Proximity (within 10 words)

    Boolean Operators:
    - "(Stockholm AND trolldom)" - Both terms required
    - "(Stockholm OR Göteborg)" - Either term (or both)
    - "(Stockholm NOT trolldom)" - First without second
    - "+Stockholm -trolldom" - Require/exclude terms

    Boosting & Grouping:
    - "Stockholm^4 troll*" - Boost term relevance (4x)
    - '(\"Stockholm dom*\"^4 Reg*)' - Boost phrase with wildcards
    - "((Stockholm OR Göteborg) AND troll*)" - Complex grouping

    TYPICAL WORKFLOW:
    1. Comprehensive search: search_transcribed(term, 0), then search_transcribed(term, 50), etc.
    2. Search related terms in parallel to build complete context
    3. Use advanced syntax for precise queries (Boolean, wildcards, fuzzy, proximity)
    4. Review hit summaries to identify most relevant documents across all searches
    5. Use browse tools (separate server) for detailed examination of specific pages

    All tools return rich, formatted text optimized for LLM understanding.
    """,
)


# Register search tool
register_search_tool(search_mcp)

from typing import Optional
from fastmcp import FastMCP
from pydantic import Field


from services import SearchOperations, SearchResultsAnalyzer, DisplayService
from formatters import MCPFormatter, format_error_message


ra_mcp = FastMCP(
    name="ra-mcp",
    instructions="""
    🏛️ Riksarkivet (RA) Search and Browse MCP Server

    This server provides access to transcribed historical documents from the Swedish National Archives.

    AVAILABLE TOOLS:

    1. 🔍 search_transcribed - Search for keywords in transcribed materials
       - Returns documents and pages containing the keyword
       - Offset parameter required to encourage comprehensive discovery
       - Context disabled by default for maximum hit coverage
       - Provides direct links to images and ALTO XML

    2. 📖 browse_document - Browse specific pages by reference code
       - View full transcriptions of specific pages
       - Supports page ranges and multiple pages
       - Optional keyword highlighting

    3. 📚 get_document_structure - Get document structure without content
       - Quick overview of available manifests
       - Document metadata and hierarchy
       - Useful for understanding what's available

    SEARCH STRATEGY FOR MAXIMUM DISCOVERY:
    1. Start with search_transcribed(keyword, offset=0) for initial hits
    2. Continue pagination with increasing offsets (50, 100, 150...) to find all matches
    3. Use show_context=False (default) to see more results per query
    4. Only enable show_context=True when you want full page text for specific hits
    5. EXPLORE RELATED TERMS: Search for similar/related words to gather comprehensive context
       - Historical variants and spellings (e.g., "trolldom" + "häxa" + "trollkona")
       - Synonyms and related concepts (e.g., "satan" + "djävul" for devil-related terms)
       - Different word forms (e.g., "trolleri" + "trollkonst" for witchcraft variants)
       - Period-appropriate terminology and archaic spellings
    6. Note reference codes and page numbers for detailed browsing
    7. Use browse_document() to view full transcriptions of interesting pages

    TYPICAL WORKFLOW:
    1. Comprehensive search: search_transcribed(term, 0), then search_transcribed(term, 50), etc.
    2. Search related terms in parallel to build complete context
    3. Review hit summaries to identify most relevant documents across all searches
    4. Use browse_document() for detailed examination of specific pages
    5. Use get_document_structure() to understand document organization

    All tools return rich, formatted text optimized for LLM understanding.
    """,
)


@ra_mcp.tool(
    name="search_transcribed",
    description="Search for keywords in transcribed historical documents from Riksarkivet",
)
async def search_transcribed(
    keyword: str,
    offset: int,
    show_context: bool = False,
    max_results: int = 10,
    max_hits_per_document: int = 3,
    max_pages_with_context: int = 0,
    context_padding: int = 0,
    max_response_tokens: int = 15000,
    truncate_page_text: int = 800,
) -> str:
    try:
        search_operations = SearchOperations()
        display_service = DisplayService(MCPFormatter())
        results_analyzer = SearchResultsAnalyzer()

        search_result = search_operations.search_transcribed(
            keyword=keyword,
            offset=offset,
            max_results=max_results,
            max_hits_per_document=max_hits_per_document,
            show_context=show_context,
            max_pages_with_context=max_pages_with_context,
            context_padding=context_padding,
        )

        if not search_result.hits:
            if offset > 0:
                return f"No more results found for '{keyword}' at offset {offset}. Total results: {search_result.total_hits}"
            return f"No results found for '{keyword}'. Try different search terms or variations."

        if show_context and search_result.enriched:
            for hit in search_result.hits:
                if hasattr(hit, "full_page_text") and hit.full_page_text:
                    if len(hit.full_page_text) > truncate_page_text:
                        hit.full_page_text = (
                            hit.full_page_text[:truncate_page_text] + "..."
                        )

        formatted_results = display_service.format_search_results(
            search_result,
            maximum_documents_to_display=max_results,
            show_full_context=show_context,
        )

        estimated_tokens = len(formatted_results) // 4
        if estimated_tokens > max_response_tokens:
            return (
                formatted_results[: max_response_tokens * 4]
                + "\n\n[Response truncated due to size limits]"
            )

        pagination_info = results_analyzer.get_pagination_info(
            search_result.hits, search_result.total_hits, offset, max_results
        )

        if pagination_info["has_more"]:
            formatted_results += f"\n\n📊 **Pagination**: Showing documents {pagination_info['document_range_start']}-{pagination_info['document_range_end']}"
            formatted_results += f"\n💡 Use `offset={pagination_info['next_offset']}` to see the next {max_results} documents"

        return formatted_results

    except Exception as e:
        return format_error_message(
            f"Search failed: {str(e)}",
            suggestions=[
                "Try a simpler search term",
                "Check if the service is available",
                "Reduce max_results or max_pages_with_context",
            ],
        )


@ra_mcp.tool(
    name="browse_document",
    description="Browse specific pages of a document by reference code",
)
async def browse_document(
    reference_code: str,
    pages: str,
    highlight_term: Optional[str] = None,
    max_pages: int = 20,
) -> str:
    """
    Browse specific pages of a document by reference code.

    Returns:
    - Full transcribed text for each requested page
    - Optional keyword highlighting
    - Direct links to images and ALTO XML

    Examples:
    - browse_document("SE/RA/420422/01", "5") - View page 5
    - browse_document("SE/RA/420422/01", "1-10") - View pages 1 through 10
    - browse_document("SE/RA/420422/01", "5,7,9", highlight_term="Stockholm") - View specific pages with highlighting
    """
    try:
        search_operations = SearchOperations()
        display_service = DisplayService(MCPFormatter())

        browse_result = search_operations.browse_document(
            reference_code=reference_code,
            pages=pages,
            highlight_term=highlight_term,
            max_pages=max_pages,
        )

        if not browse_result.contexts:
            return format_error_message(
                f"Could not load pages for {reference_code}",
                suggestions=[
                    "The pages might not have transcriptions",
                    "Try different page numbers",
                    "Check if the document is fully digitized",
                ],
            )

        return display_service.format_browse_results(browse_result, highlight_term)

    except Exception as e:
        return format_error_message(
            f"Browse failed: {str(e)}",
            suggestions=[
                "Check the reference code format",
                "Verify page numbers are valid",
                "Try with fewer pages",
            ],
        )


@ra_mcp.tool(
    name="get_document_structure",
    description="Get document structure and metadata without fetching content",
)
async def get_document_structure(
    reference_code: Optional[str] = None,
    pid: Optional[str] = None,
    include_manifest_info: bool = True,
) -> str:
    """
    Get the structure and metadata of a document without fetching page content.

    Useful for:
    - Understanding what's available in a document
    - Getting the total number of pages
    - Finding available manifests
    - Viewing document hierarchy

    Provide either reference_code or pid.
    """
    try:
        if not reference_code and not pid:
            return format_error_message(
                "Either reference_code or pid must be provided",
                suggestions=[
                    "Provide a reference code like 'SE/RA/420422/01'",
                    "Or provide a PID from search results",
                ],
            )

        search_operations = SearchOperations()
        display_service = DisplayService(MCPFormatter())

        document_structure = search_operations.get_document_structure(
            reference_code=reference_code, pid=pid
        )

        if not document_structure:
            return format_error_message(
                "Could not get structure for the document",
                suggestions=[
                    "The document might not have IIIF manifests",
                    "Try browsing specific pages instead",
                ],
            )

        return display_service.format_document_structure(document_structure)

    except Exception as e:
        return format_error_message(
            f"Failed to get document structure: {str(e)}",
            suggestions=[
                "Check the reference code or PID",
                "Try searching for the document first",
            ],
        )


@ra_mcp.resource("riksarkivet://contents/table_of_contents")
def get_table_of_contents() -> str:
    """
    Get the table of contents (Innehållsförteckning) for the Riksarkivet historical guide.
    """
    try:
        import os

        current_dir = os.path.dirname(__file__)
        markdown_path = os.path.join(
            current_dir, "..", "..", "markdown", "00_Innehallsforteckning.md"
        )

        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content

    except FileNotFoundError:
        return format_error_message(
            "Table of contents file not found",
            suggestions=[
                "Check if the markdown/00_Innehallsforteckning.md file exists",
                "Verify the file path is correct",
            ],
        )
    except Exception as e:
        return format_error_message(
            f"Failed to load table of contents: {str(e)}",
            suggestions=["Check file permissions", "Verify file encoding is UTF-8"],
        )


@ra_mcp.tool(
    name="get_guide_content",
    description="Load specific sections from the Riksarkivet historical guide",
)
async def get_guide_content(
    filename: str = Field(
        description="Markdown filename to load (e.g., '01_Domstolar.md', '02_Fangelse.md')"
    ),
) -> str:
    """
    Load content from specific sections of the Riksarkivet historical guide.
    """
    try:
        import os

        if not filename.endswith(".md"):
            return format_error_message(
                "Invalid filename format",
                suggestions=["Filename must end with .md extension"],
            )

        filename = os.path.basename(filename)
        current_dir = os.path.dirname(__file__)
        markdown_path = os.path.join(current_dir, "..", "..", "markdown", filename)

        if not os.path.exists(markdown_path):
            return format_error_message(
                f"Guide section '{filename}' not found",
                suggestions=[
                    "Check the filename spelling",
                    "Use get_table_of_contents resource to see available sections",
                    "Ensure the filename includes .md extension",
                ],
            )

        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content

    except Exception as e:
        return format_error_message(
            f"Failed to load guide content '{filename}': {str(e)}",
            suggestions=[
                "Check file permissions",
                "Verify file encoding is UTF-8",
                "Ensure the filename is valid",
            ],
        )

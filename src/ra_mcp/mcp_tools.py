"""
Refactored MCP tool definitions using shared business logic.
This eliminates code duplication with the CLI commands.
"""

from typing import Optional
from fastmcp import FastMCP
from pydantic import Field

try:
    # Try relative imports first (when used as module)
    from .services import (
        SearchOperations,
        UnifiedDisplayService,
        PlainTextFormatter,
        SearchResultsAnalyzer
    )
    from .formatters import format_error
    from .cache import get_cache
except ImportError:
    # Fall back to direct imports (when run as script)
    from services import (
        SearchOperations,
        UnifiedDisplayService,
        PlainTextFormatter,
        SearchResultsAnalyzer
    )
    from formatters import format_error
    from cache import get_cache


# Initialize FastMCP instance
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
    description="Search for keywords in transcribed historical documents from Riksarkivet"
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
    truncate_page_text: int = 800
) -> str:
    """
    Search for keywords in transcribed materials from the Swedish National Archives.

    Returns rich formatted text with:
    - Full page transcriptions with keyword highlighting
    - Document metadata and hierarchy
    - Direct links to images and transcriptions
    - Context pages around each hit for better understanding

    Parameters:
    - keyword: The search term
    - offset: Start position in search results for pagination (required for more hits)
    - show_context: Include full page text (default False)
    - max_results: Maximum number of documents to fetch (default 10)
    - max_hits_per_document: Maximum page hits to return per document (default 3)
    - max_pages_with_context: Maximum pages to enrich with full text (default 0)
    - context_padding: Pages of context around each hit (default 0)
    - max_response_tokens: Approximate max tokens in response to prevent overflow (default 15000)
    - truncate_page_text: Max characters per page text to prevent huge responses (default 800)

    Example:
    - search_transcribed("häxor", offset=0) - Find documents about witches
    - search_transcribed("Stockholm", offset=0, show_context=True, max_pages_with_context=10) - Find Stockholm references with context
    - search_transcribed("näcken", offset=10, max_results=10) - Get results 11-20
    - search_transcribed("näcken", offset=0, max_pages_with_context=3, context_padding=0) - Limit response size
    """
    try:
        # Use shared business logic
        search_ops = SearchOperations()
        display_service = UnifiedDisplayService(PlainTextFormatter())
        analyzer = SearchResultsAnalyzer()
        cache = get_cache()

        # Check cache for search results
        cache_params = {
            'keyword': keyword,
            'max_results': max_results,
            'offset': offset,
            'max_hits_per_document': max_hits_per_document
        }
        cached_result = cache.get('search', cache_params)

        if cached_result is None:
            # Perform search using shared logic
            operation = search_ops.search_transcribed(
                keyword=keyword,
                offset=offset,
                max_results=max_results,
                max_hits_per_document=max_hits_per_document,
                show_context=show_context,
                max_pages_with_context=max_pages_with_context,
                context_padding=context_padding
            )
            cache.set('search', cache_params, operation)
        else:
            operation = cached_result

        if not operation.hits:
            if offset > 0:
                return f"No more results found for '{keyword}' at offset {offset}. Total results: {operation.total_hits}"
            return f"No results found for '{keyword}'. Try different search terms or variations."

        # Apply text truncation if needed
        if show_context and operation.enriched:
            for hit in operation.hits:
                if hasattr(hit, 'full_page_text') and hit.full_page_text:
                    if len(hit.full_page_text) > truncate_page_text:
                        hit.full_page_text = hit.full_page_text[:truncate_page_text] + "..."

        # Format results using shared display service
        formatted = display_service.format_search_results(
            operation,
            max_display=max_results,
            show_context=show_context
        )

        # Check token count and add pagination info
        estimated_tokens = len(formatted) // 4
        if estimated_tokens > max_response_tokens:
            return formatted[:max_response_tokens * 4] + "\n\n[Response truncated due to size limits]"

        # Add pagination info
        pagination_info = analyzer.get_pagination_info(
            operation.hits, operation.total_hits, offset, max_results
        )

        if pagination_info['has_more']:
            formatted += f"\n\n📊 **Pagination**: Showing documents {pagination_info['document_range_start']}-{pagination_info['document_range_end']}"
            formatted += f"\n💡 Use `offset={pagination_info['next_offset']}` to see the next {max_results} documents"

        return formatted

    except Exception as e:
        return format_error(
            f"Search failed: {str(e)}",
            suggestions=[
                "Try a simpler search term",
                "Check if the service is available",
                "Reduce max_results or max_pages_with_context"
            ]
        )


@ra_mcp.tool(
    name="browse_document",
    description="Browse specific pages of a document by reference code"
)
async def browse_document(
    reference_code: str,
    pages: str,
    highlight_term: Optional[str] = None,
    max_pages: int = 20
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
        # Use shared business logic
        search_ops = SearchOperations()
        display_service = UnifiedDisplayService(PlainTextFormatter())

        # Perform browse using shared logic
        operation = search_ops.browse_document(
            reference_code=reference_code,
            pages=pages,
            highlight_term=highlight_term,
            max_pages=max_pages
        )

        if not operation.contexts:
            return format_error(
                f"Could not load pages for {reference_code}",
                suggestions=[
                    "The pages might not have transcriptions",
                    "Try different page numbers",
                    "Check if the document is fully digitized"
                ]
            )

        # Format results using shared display service
        return display_service.format_browse_results(operation, highlight_term)

    except Exception as e:
        return format_error(
            f"Browse failed: {str(e)}",
            suggestions=[
                "Check the reference code format",
                "Verify page numbers are valid",
                "Try with fewer pages"
            ]
        )


@ra_mcp.tool(
    name="get_document_structure",
    description="Get document structure and metadata without fetching content"
)
async def get_document_structure(
    reference_code: Optional[str] = None,
    pid: Optional[str] = None,
    include_manifest_info: bool = True
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
            return format_error(
                "Either reference_code or pid must be provided",
                suggestions=["Provide a reference code like 'SE/RA/420422/01'", "Or provide a PID from search results"]
            )

        # Use shared business logic
        search_ops = SearchOperations()
        display_service = UnifiedDisplayService(PlainTextFormatter())

        # Get document structure using shared logic
        collection_info = search_ops.get_document_structure(
            reference_code=reference_code,
            pid=pid
        )

        if not collection_info:
            return format_error(
                f"Could not get structure for the document",
                suggestions=["The document might not have IIIF manifests", "Try browsing specific pages instead"]
            )

        # Format results using shared display service
        return display_service.format_document_structure(collection_info)

    except Exception as e:
        return format_error(
            f"Failed to get document structure: {str(e)}",
            suggestions=["Check the reference code or PID", "Try searching for the document first"]
        )


# Keep the existing resource and guide content tools as they are
@ra_mcp.resource("riksarkivet://contents/table_of_contents")
def get_table_of_contents() -> str:
    """
    Get the table of contents (Innehållsförteckning) for the Riksarkivet historical guide.
    """
    try:
        import os
        current_dir = os.path.dirname(__file__)
        markdown_path = os.path.join(current_dir, "..", "..", "markdown", "00_Innehallsforteckning.md")

        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    except FileNotFoundError:
        return format_error(
            "Table of contents file not found",
            suggestions=[
                "Check if the markdown/00_Innehallsforteckning.md file exists",
                "Verify the file path is correct"
            ]
        )
    except Exception as e:
        return format_error(
            f"Failed to load table of contents: {str(e)}",
            suggestions=["Check file permissions", "Verify file encoding is UTF-8"]
        )


@ra_mcp.tool(
    name="get_guide_content",
    description="Load specific sections from the Riksarkivet historical guide"
)
async def get_guide_content(
    filename: str = Field(description="Markdown filename to load (e.g., '01_Domstolar.md', '02_Fangelse.md')")
) -> str:
    """
    Load content from specific sections of the Riksarkivet historical guide.
    """
    try:
        import os

        # Validate filename
        if not filename.endswith('.md'):
            return format_error(
                "Invalid filename format",
                suggestions=["Filename must end with .md extension"]
            )

        filename = os.path.basename(filename)
        current_dir = os.path.dirname(__file__)
        markdown_path = os.path.join(current_dir, "..", "..", "markdown", filename)

        if not os.path.exists(markdown_path):
            return format_error(
                f"Guide section '{filename}' not found",
                suggestions=[
                    "Check the filename spelling",
                    "Use get_table_of_contents resource to see available sections",
                    "Ensure the filename includes .md extension"
                ]
            )

        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    except Exception as e:
        return format_error(
            f"Failed to load guide content '{filename}': {str(e)}",
            suggestions=[
                "Check file permissions",
                "Verify file encoding is UTF-8",
                "Ensure the filename is valid"
            ]
        )
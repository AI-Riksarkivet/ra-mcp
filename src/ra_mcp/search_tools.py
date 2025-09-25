from typing import Optional
from fastmcp import FastMCP


from .services import SearchOperations, analysis, DisplayService
from .formatters import MCPFormatter, format_error_message


search_mcp = FastMCP(
    name="ra-search-mcp",
    description="Riksarkivet search server providing access to transcribed historical documents with 3 tools (search_transcribed, browse_document, get_document_structure) and 2 resources (table_of_contents, guide sections)",
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

    AVAILABLE RESOURCES:

    1. 📑 riksarkivet://contents/table_of_contents - Get table of contents
       - Returns the complete guide index (Innehållsförteckning)
       - Lists all available historical guide sections

    2. 📄 riksarkivet://guide/{filename} - Load specific guide sections
       - Access detailed historical documentation by filename
       - Examples: '01_Domstolar.md', '02_Fangelse.md'
       - Use table_of_contents to see available sections

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
    6. Access guide resources for historical context and documentation

    All tools return rich, formatted text optimized for LLM understanding.
    """,
)


@search_mcp.tool(
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

        search_result = await _execute_search_query(
            search_operations,
            keyword=keyword,
            offset=offset,
            max_results=max_results,
            max_hits_per_document=max_hits_per_document,
            show_context=show_context,
            max_pages_with_context=max_pages_with_context,
            context_padding=context_padding,
        )

        if not search_result.hits:
            return _generate_no_results_message(
                keyword, offset, search_result.total_hits
            )

        if show_context and search_result.enriched:
            _truncate_page_texts_if_needed(search_result.hits, truncate_page_text)

        formatted_results = display_service.format_search_results(
            search_result,
            maximum_documents_to_display=max_results,
            show_full_context=show_context,
        )

        formatted_results = _apply_token_limit_if_needed(
            formatted_results, max_response_tokens
        )

        formatted_results = _append_pagination_info_if_needed(
            formatted_results, search_result, offset, max_results
        )

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


async def _execute_search_query(search_operations, **search_params):
    """Execute the search query with the given parameters."""
    return search_operations.search_transcribed(**search_params)


def _generate_no_results_message(keyword, offset, total_hits):
    """Generate appropriate message when no results are found."""
    if offset > 0:
        return f"No more results found for '{keyword}' at offset {offset}. Total results: {total_hits}"
    return (
        f"No results found for '{keyword}'. Try different search terms or variations."
    )


def _truncate_page_texts_if_needed(hits, max_length):
    """Truncate page texts that exceed the maximum length."""
    for hit in hits:
        if hasattr(hit, "full_page_text") and hit.full_page_text:
            if len(hit.full_page_text) > max_length:
                hit.full_page_text = hit.full_page_text[:max_length] + "..."


def _apply_token_limit_if_needed(formatted_results, max_response_tokens):
    """Apply token limit to the formatted results if needed."""
    estimated_tokens = len(formatted_results) // 4
    if estimated_tokens > max_response_tokens:
        return (
            formatted_results[: max_response_tokens * 4]
            + "\n\n[Response truncated due to size limits]"
        )
    return formatted_results


def _append_pagination_info_if_needed(
    formatted_results, search_result, offset, max_results
):
    """Append pagination information to results if there are more results available."""
    pagination_info = analysis.get_pagination_info(
        search_result.hits, search_result.total_hits, offset, max_results
    )

    if pagination_info["has_more"]:
        formatted_results += f"\n\n📊 **Pagination**: Showing documents {pagination_info['document_range_start']}-{pagination_info['document_range_end']}"
        formatted_results += f"\n💡 Use `offset={pagination_info['next_offset']}` to see the next {max_results} documents"

    return formatted_results


@search_mcp.tool(
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

        browse_result = await _fetch_document_pages(
            search_operations,
            reference_code=reference_code,
            pages=pages,
            highlight_term=highlight_term,
            max_pages=max_pages,
        )

        if not browse_result.contexts:
            return _generate_no_pages_found_message(reference_code)

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


async def _fetch_document_pages(search_operations, **browse_params):
    """Fetch document pages with the given parameters."""
    return search_operations.browse_document(**browse_params)


def _generate_no_pages_found_message(reference_code):
    """Generate error message when no pages are found."""
    return format_error_message(
        f"Could not load pages for {reference_code}",
        suggestions=[
            "The pages might not have transcriptions",
            "Try different page numbers",
            "Check if the document is fully digitized",
        ],
    )


@search_mcp.tool(
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
        if not _validate_document_identifiers(reference_code, pid):
            return _generate_missing_identifier_message()

        search_operations = SearchOperations()
        display_service = DisplayService(MCPFormatter())

        document_structure = await _fetch_document_structure(
            search_operations, reference_code=reference_code, pid=pid
        )

        if not document_structure:
            return _generate_structure_not_found_message()

        return display_service.format_document_structure(document_structure)

    except Exception as e:
        return format_error_message(
            f"Failed to get document structure: {str(e)}",
            suggestions=[
                "Check the reference code or PID",
                "Try searching for the document first",
            ],
        )


def _validate_document_identifiers(reference_code, pid):
    """Validate that at least one document identifier is provided."""
    return reference_code or pid


async def _fetch_document_structure(search_operations, **params):
    """Fetch the document structure with the given parameters."""
    return search_operations.get_document_structure(**params)


def _generate_missing_identifier_message():
    """Generate error message for missing document identifiers."""
    return format_error_message(
        "Either reference_code or pid must be provided",
        suggestions=[
            "Provide a reference code like 'SE/RA/420422/01'",
            "Or provide a PID from search results",
        ],
    )


def _generate_structure_not_found_message():
    """Generate error message when document structure cannot be retrieved."""
    return format_error_message(
        "Could not get structure for the document",
        suggestions=[
            "The document might not have IIIF manifests",
            "Try browsing specific pages instead",
        ],
    )


@search_mcp.resource("riksarkivet://contents/table_of_contents")
def get_table_of_contents() -> str:
    """
    Get the table of contents (Innehållsförteckning) for the Riksarkivet historical guide.
    """
    try:
        content = _load_markdown_file("00_Innehallsforteckning.md")
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


@search_mcp.resource("riksarkivet://guide/{filename}")
def get_guide_content(filename: str) -> str:
    """
    Load content from specific sections of the Riksarkivet historical guide.

    Args:
        filename: Markdown filename to load (e.g., '01_Domstolar.md', '02_Fangelse.md')

    Returns:
        The content of the requested guide section
    """
    try:
        if not _validate_markdown_filename(filename):
            return _generate_invalid_filename_message()

        if not _check_file_exists(filename):
            return _generate_file_not_found_message(filename)

        content = _load_markdown_file(filename)
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


def _validate_markdown_filename(filename):
    """Validate that the filename has .md extension."""
    return filename.endswith(".md")


def _generate_invalid_filename_message():
    """Generate error message for invalid filename format."""
    return format_error_message(
        "Invalid filename format",
        suggestions=["Filename must end with .md extension"],
    )


def _check_file_exists(filename):
    """Check if the markdown file exists."""
    import os

    filename = os.path.basename(filename)
    current_dir = os.path.dirname(__file__)
    markdown_path = os.path.join(current_dir, "..", "..", "markdown", filename)
    return os.path.exists(markdown_path)


def _generate_file_not_found_message(filename):
    """Generate error message when file is not found."""
    return format_error_message(
        f"Guide section '{filename}' not found",
        suggestions=[
            "Check the filename spelling",
            "Use get_table_of_contents resource to see available sections",
            "Ensure the filename includes .md extension",
        ],
    )


def _load_markdown_file(filename):
    """Load content from a markdown file."""
    import os

    filename = os.path.basename(filename)
    current_dir = os.path.dirname(__file__)
    markdown_path = os.path.join(current_dir, "..", "..", "markdown", filename)

    with open(markdown_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

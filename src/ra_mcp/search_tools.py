import os
from typing import Optional
from fastmcp import FastMCP


from .services import SearchOperations, BrowseOperations
from .services.display_service import DisplayService
from .formatters import format_error_message, PlainTextFormatter
from .utils.http_client import default_http_client


search_mcp = FastMCP(
    name="ra-search-mcp",
    instructions="""
    🏛️ Riksarkivet (RA) Search and Browse MCP Server

    This server provides access to transcribed historical documents from the Swedish National Archives.

    AVAILABLE TOOLS:

    1. 🔍 search_transcribed - Search for keywords in transcribed materials
       - Returns documents and pages containing the keyword (a subset of what is written on the document)
       - Offset parameter required to encourage comprehensive discovery
       - Provides direct links to images and ALTO XML
       - Supports advanced Solr search syntax (see SEARCH SYNTAX below)

    2. 📖 browse_document - Browse specific pages by reference code
       - View full transcriptions of specific pages
       - Supports page ranges and multiple pages

    AVAILABLE RESOURCES:

    1. 📑 riksarkivet://contents/table_of_contents - Get table of contents
       - Returns the complete guide index (Innehållsförteckning)
       - Lists all available historical guide sections

    2. 📄 riksarkivet://guide/{filename} - Load specific guide sections
       - Access detailed historical documentation by filename
       - Examples: '01_Domstolar.md', '02_Fangelse.md'
       - Use table_of_contents to see available sections

    SEARCH STRATEGY FOR MAXIMUM DISCOVERY:
    1. Start with search_transcribed(keyword, offset=0) for initial hits (use syntax guide bellow when searching)
    2. Continue pagination with increasing offsets (50, 100, 150...) to find all matches
    3. EXPLORE RELATED TERMS: Search for similar/related words to gather comprehensive context
       - Historical variants and spellings (e.g., "trolldom" + "häxa" + "trollkona")
       - Synonyms and related concepts (e.g., "satan" + "djävul" for devil-related terms)
       - Different word forms (e.g., "trolleri" + "trollkonst" for witchcraft variants)
       - Period-appropriate terminology and archaic spellings
    4. Note reference codes and page numbers for detailed browsing
    5. Use browse_document() to view full transcriptions of interesting pages

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
    5. Use browse_document() for detailed examination of specific pages
    6. Access guide resources for historical context and documentation

    All tools return rich, formatted text optimized for LLM understanding.
    """,
)


@search_mcp.tool(
    name="search_transcribed",
    description="""Search for keywords in transcribed historical documents from the Swedish National Archives (Riksarkivet).

    This tool searches through historical documents and returns matching pages with their transcriptions.
    Supports advanced Solr query syntax including wildcards, fuzzy search, Boolean operators, and proximity searches.

    Key features:
    - Returns document metadata, page numbers, and text snippets containing the keyword
    - Provides direct links to page images and ALTO XML transcriptions
    - Supports pagination via offset parameter for comprehensive discovery
    - Advanced search syntax for precise queries

    Search syntax examples:
    - Basic: "Stockholm" - exact term search
    - Wildcards: "Stock*", "St?ckholm", "*holm" - match patterns
    - Fuzzy: "Stockholm~" or "Stockholm~1" - find similar words (typos, variants)
    - Proximity: '\"Stockholm trolldom\"~10' - words within 10 words of each other
    - Boolean: "(Stockholm AND trolldom)", "(Stockholm OR Göteborg)", "(Stockholm NOT trolldom)"
    - Boosting: \"Stockholm^4 trol*\" - increase relevance of specific terms
    - Complex: "((troll* OR häx*) AND (Stockholm OR Göteborg))" - combine operators

    NOTE: make sure to use grouping () for any boolean search also  \"\" is important to group multiple words
    E.g do '((skatt* OR guld* OR silver*) AND (stöld* OR stul*))' instead of '(skatt* OR guld* OR silver*) AND (stöld* OR stul*)', i.e prefer grouping as that will retrun results, non-grouping will return 0 results 

    also prefer to use fuzzy search i.e. something like ((stöld~2 OR tjufnad~2) AND (silver* OR guld*)) AND (döm* OR straff*) as many trancriptions are OCR/HTR AI based with common errors. Also account for old swedish i.e (((präst* OR prest*) OR (kyrko* OR kyrck*)) AND ((silver* OR silfv*) OR (guld* OR gull*)))

    Proximity guide:

        Use quotes around the search terms

        "term1 term2"~N ✅
        term1 term2~N ❌

        Only 2 terms work reliably

        "kyrka stöld"~10 ✅
        "kyrka silver stöld"~10 ❌

        The number indicates maximum word distance

        ~3 = within 3 words
        ~10 = within 10 words
        ~50 = within 50 words

        📊 Working Examples by Category:
        Crime & Punishment:
        "tredje stöld"~5           # Third-time theft
        "dömd hänga"~10            # Sentenced to hang  
        "inbrott natt*"~5          # Burglary at night
        "kyrka stöld"~10           # Church theft
        Values & Items:
        "hundra daler"~3           # Hundred dalers
        "stor* stöld*"~5           # Major theft
        "guld* ring*"~10           # Gold ring
        "silver* kalk*"~10         # Silver chalice
        Complex Combinations:
        ("kyrka stöld"~10 OR "kyrka tjuv*"~10) AND 17*
        # Church thefts or church thieves in 1700s

        ("inbrott natt*"~5) AND (guld* OR silver*)  
        # Night burglaries involving gold or silver

        ("första resan" AND stöld*) OR ("tredje stöld"~5)
        # First-time theft OR third theft (within proximity)
        🔧 Troubleshooting Tips:
        If proximity search returns no results:

        Check your quotes - Must wrap both terms
        Reduce to 2 terms - Drop extra words
        Try exact terms first - Before wildcards
        Increase distance - Try ~10 instead of ~3
        Simplify wildcards - Use on one term only

        💡 Advanced Strategy:
        Layer your searches from simple to complex:
        Step 1: "kyrka stöld"~10
        Step 2: ("kyrka stöld"~10 OR "kyrka tjuv*"~10)
        Step 3: (("kyrka stöld"~10 OR "kyrka tjuv*"~10) AND 17*)
        Step 4: (("kyrka stöld"~10 OR "kyrka tjuv*"~10) AND 17*) AND (guld* OR silver*)
        Most Reliable Proximity Patterns:

        Exact + Exact: "hundra daler"~3
        Exact + Wildcard: "inbrott natt*"~5
        Wildcard + Wildcard (sometimes): "stor* stöld*"~5

        The key is that proximity operators in this system work best with exactly 2 terms in quotes, and you can then combine multiple proximity searches using Boolean operators outside the quotes!



    Parameters:
    - keyword: Search term or Solr query (required)
    - offset: Starting position for pagination - use 0, then 50, 100, etc. (required)
    - max_results: Maximum documents to return per query (default: 10)
    - max_hits_per_document: Maximum matching pages per document (default: 3)
    - max_response_tokens: Maximum tokens in response (default: 15000)

    Best practices:
    - Start with offset=0 and increase by 50 to discover all matches
    - Search related terms and variants for comprehensive coverage
    - Use wildcards (*) for word variations: "troll*" finds "trolldom", "trolleri", "trollkona"
    - Use fuzzy search (~) for historical spelling variants
    - Use browse_document tool to view full page transcriptions of interesting results
    """,
)
async def search_transcribed(
    keyword: str,
    offset: int,
    max_results: int = 50,
    max_hits_per_document: int = 3,
    max_response_tokens: int = 15000,
) -> str:
    try:
        search_operations = SearchOperations(http_client=default_http_client)
        display_service = DisplayService(formatter=PlainTextFormatter())

        search_result = search_operations.search_transcribed(
            keyword=keyword,
            offset=offset,
            max_results=max_results,
            max_hits_per_document=max_hits_per_document,
        )

        formatted_results = display_service.format_search_results(
            search_result,
            maximum_documents_to_display=max_results,
        )

        formatted_results = _apply_token_limit_if_needed(formatted_results, max_response_tokens)

        formatted_results = _append_pagination_info_if_needed(formatted_results, search_result, offset, max_results)

        return formatted_results

    except Exception as e:
        return format_error_message(
            f"Search failed: {str(e)}",
            error_suggestions=[
                "Try a simpler search term",
                "Check if the service is available",
                "Reduce max_results",
            ],
        )


def _apply_token_limit_if_needed(formatted_results, max_response_tokens):
    """Apply token limit to the formatted results if needed."""
    estimated_tokens = len(formatted_results) // 4
    if estimated_tokens > max_response_tokens:
        return formatted_results[: max_response_tokens * 4] + "\n\n[Response truncated due to size limits]"
    return formatted_results


def _extract_unique_documents(search_hits):
    """Extract unique document identifiers from hits."""
    unique_documents = set()
    for hit in search_hits:
        document_id = hit.reference_code or hit.pid
        unique_documents.add(document_id)
    return unique_documents


def _calculate_pagination_metadata(unique_documents, search_hits, total_hits, offset, limit):
    """Calculate pagination metadata."""
    has_additional_results = len(unique_documents) == limit and total_hits > len(search_hits)

    document_range_start = offset // limit * limit + 1
    document_range_end = document_range_start + len(unique_documents) - 1
    next_page_offset = offset + limit if has_additional_results else None

    return {
        "total_hits": total_hits,
        "total_documents_shown": len(unique_documents),
        "total_page_hits": len(search_hits),
        "document_range_start": document_range_start,
        "document_range_end": document_range_end,
        "has_more": has_additional_results,
        "next_offset": next_page_offset,
    }


def _get_pagination_info(search_hits, total_hit_count, pagination_offset, result_limit):
    """Calculate pagination information for search results.

    Args:
        search_hits: List of search hits
        total_hit_count: Total number of hits
        pagination_offset: Current offset
        result_limit: Maximum results per page

    Returns:
        Dictionary with pagination metadata
    """
    unique_document_identifiers = _extract_unique_documents(search_hits)

    pagination_metadata = _calculate_pagination_metadata(
        unique_document_identifiers,
        search_hits,
        total_hit_count,
        pagination_offset,
        result_limit,
    )

    return pagination_metadata


def _append_pagination_info_if_needed(formatted_results, search_result, offset, max_results):
    """Append pagination information to results if there are more results available."""
    pagination_info = _get_pagination_info(search_result.hits, search_result.total_hits, offset, max_results)

    if pagination_info["has_more"]:
        formatted_results += f"\n\n📊 **Pagination**: Showing documents {pagination_info['document_range_start']}-{pagination_info['document_range_end']}"
        formatted_results += f"\n💡 Use `offset={pagination_info['next_offset']}` to see the next {max_results} documents"

    return formatted_results


@search_mcp.tool(
    name="browse_document",
    description="""Browse specific pages of a document by reference code and view full transcriptions.

    This tool retrieves complete page transcriptions from historical documents in Swedish.
    Each result includes the full transcribed text as it appears in the original document,
    plus direct links to view the original page images in Riksarkivet's image viewer (bildvisaren).
    Prefer showing the whole transcription and link in responses of individual pages. 
    Download some of the nearby pages too on selected pages if context seem to be missing from the trancript 
    to get a better picture

    Original text:
    transcript

    Translation
    Modern translation in language of user 

    Links

    Key features:
    - Returns full page transcriptions in (original language)
    - Provides links to bildvisaren (Riksarkivet's image viewer) for viewing original documents
    - Supports single pages, page ranges, or multiple specific pages
    - Direct links to ALTO XML for detailed text layout information

    Parameters:
    - reference_code: Document reference code from search results (e.g., "SE/RA/420422/01")
    - pages: Page specification - single ("5"), range ("1-10"), or comma-separated ("5,7,9")
    - highlight_term: Optional keyword to highlight in the transcription
    - max_pages: Maximum number of pages to retrieve (default: 20)

    Examples:
    - browse_document("SE/RA/420422/01", "5") - View full transcription of page 5
    - browse_document("SE/RA/420422/01", "1-10") - View pages 1 through 10
    - browse_document("SE/RA/420422/01", "5,7,9", highlight_term="Stockholm") - View specific pages with highlighting

    Note: Transcriptions are as they appear in the historical documents.
    Use this tool when you need complete page content rather than just search snippets.
    """,
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
        browse_operations = BrowseOperations(http_client=default_http_client)
        display_service = DisplayService(formatter=PlainTextFormatter())

        browse_result = _fetch_document_pages(
            browse_operations,
            reference_code=reference_code,
            pages=pages,
            highlight_term=highlight_term,
            max_pages=max_pages,
        )

        if not browse_result.contexts:
            return _generate_no_pages_found_message(reference_code)

        result = display_service.format_browse_results(browse_result, highlight_term)
        # MCPFormatter always returns string, but type hints include List for RichConsoleFormatter
        return result if isinstance(result, str) else str(result)

    except Exception as e:
        return format_error_message(
            f"Browse failed: {str(e)}",
            error_suggestions=[
                "Check the reference code format",
                "Verify page numbers are valid",
                "Try with fewer pages",
            ],
        )


def _fetch_document_pages(browse_operations, **browse_params):
    """Fetch document pages with the given parameters."""
    return browse_operations.browse_document(**browse_params)


def _generate_no_pages_found_message(reference_code):
    """Generate error message when no pages are found."""
    return format_error_message(
        f"Could not load pages for {reference_code}",
        error_suggestions=[
            "The pages might not have transcriptions",
            "Try different page numbers",
            "Check if the document is fully digitized",
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
            error_suggestions=[
                "Check if the markdown/00_Innehallsforteckning.md file exists",
                "Verify the file path is correct",
            ],
        )
    except Exception as e:
        return format_error_message(
            f"Failed to load table of contents: {str(e)}",
            error_suggestions=[
                "Check file permissions",
                "Verify file encoding is UTF-8",
            ],
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
            error_suggestions=[
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
        error_suggestions=["Filename must end with .md extension"],
    )


def _check_file_exists(filename):
    """Check if the markdown file exists."""
    filename = os.path.basename(filename)
    current_dir = os.path.dirname(__file__)
    markdown_path = os.path.join(current_dir, "..", "..", "markdown", filename)
    return os.path.exists(markdown_path)


def _generate_file_not_found_message(filename):
    """Generate error message when file is not found."""
    return format_error_message(
        f"Guide section '{filename}' not found",
        error_suggestions=[
            "Check the filename spelling",
            "Use get_table_of_contents resource to see available sections",
            "Ensure the filename includes .md extension",
        ],
    )


def _load_markdown_file(filename):
    """Load content from a markdown file."""
    filename = os.path.basename(filename)
    current_dir = os.path.dirname(__file__)
    markdown_path = os.path.join(current_dir, "..", "..", "markdown", filename)

    with open(markdown_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

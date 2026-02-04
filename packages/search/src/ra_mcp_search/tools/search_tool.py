"""
Search MCP tool for Riksarkivet transcribed documents.

Provides the search_transcribed tool with pagination and formatting helpers.
"""

import logging

from ra_mcp_core.formatters import format_error_message
from ..formatters import PlainTextFormatter
from ra_mcp_core.utils.http_client import default_http_client

from ..services import SearchOperations
from ..services.search_display_service import SearchDisplayService


logger = logging.getLogger(__name__)


def register_search_tool(mcp) -> None:
    """Register the search tool with the MCP server."""

    @mcp.tool(
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
    - max_snippets_per_record: Maximum matching pages per document (default: 3)
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
        max_results: int = 25,
        max_snippets_per_record: int = 3,
        max_response_tokens: int = 15000,
    ) -> str:
        logger.info(f"MCP Tool: search_transcribed called with keyword='{keyword}', offset={offset}, max_results={max_results}")

        try:
            logger.debug("Initializing search operations...")
            search_operations = SearchOperations(http_client=default_http_client)
            search_display_service = SearchDisplayService(formatter=PlainTextFormatter())

            logger.info(f"Executing search for '{keyword}'...")
            search_result = search_operations.search_transcribed(
                keyword=keyword,
                offset=offset,
                max_results=max_results,
                max_snippets_per_record=max_snippets_per_record,
            )

            logger.info(f"Formatting {len(search_result.items)} search results...")
            formatted_results = search_display_service.format_search_results(
                search_result,
                maximum_documents_to_display=max_results,
            )

            formatted_results = _apply_token_limit_if_needed(formatted_results, max_response_tokens)
            formatted_results = _append_pagination_info_if_needed(formatted_results, search_result, offset, max_results)

            logger.info("✓ Search completed successfully, returning results")
            return formatted_results

        except Exception as e:
            logger.error(f"✗ MCP search_transcribed failed: {type(e).__name__}: {e}", exc_info=True)
            return format_error_message(
                f"Search failed: {str(e)}",
                error_suggestions=[
                    "Try a simpler search term",
                    "Check if the service is available",
                    "Reduce max_results",
                    "Check Hugging Face logs for timeout details",
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

"""
Search MCP tool for Riksarkivet transcribed documents.

Provides the search_transcribed tool with pagination and formatting helpers.
"""

import logging
import re
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

from ra_mcp_common.formatting import page_id_to_number
from ra_mcp_common.http_client import default_http_client
from ra_mcp_common.telemetry import mark_span_error
from ra_mcp_search_lib.config import MAX_LIMIT
from ra_mcp_search_lib.search_operations import SearchOperations
from ra_mcp_search_lib.validation import validate_search_query

from .formatter import PlainTextFormatter


logger = logging.getLogger("ra_mcp.search.tool")


_VALID_SORT_VALUES = {"relevance", "timeAsc", "timeDesc", "alphaAsc", "alphaDesc"}

# Swedish archival reference codes look like "SE/RA/420422", "SE/LLA/10933/F II a"
# or "SE/O258G/GSA/1061": country "SE", a short institution code (letters and/or
# digits — municipal archives like O258G contain digits), then an optional
# archive/series/volume path. A bare prefix like "SE/RA" is equally pathological
# as free text, so it is matched too. The 2-6 length cap keeps prose run-ins from
# real NAD descriptions (e.g. "SE/Admavdelning") searchable. Pattern validated
# against 303K distinct codes extracted from NAD EAD XML (99.996% before widening).
_REFERENCE_CODE_PATTERN = re.compile(r"^SE/[A-Za-zÅÄÖåäö0-9]{2,6}(?:/\S|/?$)", re.IGNORECASE)


def _looks_like_reference_code(keyword: str) -> bool:
    """Return True if the keyword is an archival reference code (signum), not a search term.

    Reference codes must never be sent to the free-text search API: it tokenizes them
    (SE, RA, single letters like "F"/"II"/"a") and OR-matches nearly the entire catalog,
    yielding multi-second, multi-megabyte responses with useless results. Such codes are
    resolved by browse_document (OAI-PMH), not by search.
    """
    return bool(_REFERENCE_CODE_PATTERN.match(keyword.strip()))


def _validate_search_input(keyword: str, offset: int, year_min: int | None, year_max: int | None, sort: str = "relevance", limit: int = 25) -> str | None:
    """Validate common search inputs. Returns an error string or None if valid."""
    if not keyword or not keyword.strip():
        mark_span_error("keyword must not be empty", error_type="validation")
        return PlainTextFormatter().format_error_message("keyword must not be empty", error_suggestions=["Provide a search term, e.g. 'Stockholm'"])
    if _looks_like_reference_code(keyword):
        mark_span_error("keyword is an archival reference code", error_type="validation")
        return PlainTextFormatter().format_error_message(
            f"'{keyword.strip()}' looks like an archival reference code, not a search term. "
            "The search API only does free-text matching and cannot look up records by reference code — "
            "it would match the entire catalog and be very slow.",
            error_suggestions=[
                f"To find records under this code, search the exact phrase in quotes: keyword='\"{keyword.strip()}\"'",
                f"To read a volume's pages, use browse_document with reference_code='{keyword.strip()}'",
                "To search by content instead, use plain keywords (e.g. a name, place, or subject)",
            ],
        )
    query_error = validate_search_query(keyword)
    if query_error:
        mark_span_error(query_error, error_type="validation")
        return PlainTextFormatter().format_error_message(
            query_error,
            error_suggestions=["Group Boolean logic with matching parentheses, e.g. (Stockholm OR Göteborg), and pair every quote."],
        )
    if offset < 0:
        mark_span_error(f"offset must be >= 0, got {offset}", error_type="validation")
        return PlainTextFormatter().format_error_message(f"offset must be >= 0, got {offset}", error_suggestions=["Use offset=0 for the first page of results"])
    if limit < 1:
        mark_span_error(f"limit must be >= 1, got {limit}", error_type="validation")
        return PlainTextFormatter().format_error_message(f"limit must be >= 1, got {limit}", error_suggestions=["Use limit=25 for default page size"])
    if limit > MAX_LIMIT:
        mark_span_error(f"limit must be <= {MAX_LIMIT}, got {limit}", error_type="validation")
        return PlainTextFormatter().format_error_message(
            f"limit must be <= {MAX_LIMIT}, got {limit}",
            error_suggestions=[f"Use a smaller limit (max {MAX_LIMIT}) and paginate with offset for more results"],
        )
    if year_min is not None and year_max is not None and year_min > year_max:
        mark_span_error(f"year_min ({year_min}) must be <= year_max ({year_max})", error_type="validation")
        return PlainTextFormatter().format_error_message(f"year_min ({year_min}) must be <= year_max ({year_max})")
    if sort not in _VALID_SORT_VALUES:
        mark_span_error(f"Invalid sort value '{sort}'", error_type="validation")
        return PlainTextFormatter().format_error_message(
            f"Invalid sort value '{sort}'",
            error_suggestions=[f"Valid values: {', '.join(sorted(_VALID_SORT_VALUES))}"],
        )
    return None


def register_search_tool(mcp: FastMCP) -> None:
    """Register the search tools with the MCP server."""

    @mcp.tool(
        name="transcribed",
        version="1.0",
        timeout=30.0,
        tags={"search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search AI-transcribed text in digitised historical documents from the Swedish National Archives. "
            "IMPORTANT: Transcriptions are AI-generated (HTR/OCR) and contain recognition errors — "
            "always use fuzzy search (~) to compensate for misread characters and increase hits.\n"
            'Supports Solr syntax: wildcards (troll*), fuzzy (stockholm~1), Boolean ((A AND B)), proximity ("term1 term2"~10). '
            "Always group Boolean queries with outer parentheses. Use fuzzy (~) for OCR/HTR errors and old Swedish variants (präst/prest, silver/silfver).\n"
            "Paginate with offset (0, 50, 100...). Session dedup: re-calling returns stubs for already-seen documents."
        ),
    )
    async def search_transcribed(
        keyword: Annotated[
            str, Field(description='Search term or Solr query. Supports wildcards (*), fuzzy (~), Boolean (AND/OR/NOT), proximity ("term1 term2"~N).')
        ],
        offset: Annotated[int, Field(description="Pagination start position. Use 0 for first page, then 50, 100, etc.")],
        limit: Annotated[int, Field(description="Maximum documents to return per query.")] = 25,
        max_snippets_per_record: Annotated[int, Field(description="Maximum matching pages shown per document.", ge=1)] = 3,
        max_response_tokens: Annotated[int, Field(description="Maximum tokens in response.", ge=1000)] = 15000,
        sort: Annotated[str, Field(description="Sort order: 'relevance', 'timeAsc', 'timeDesc', 'alphaAsc', 'alphaDesc'.")] = "relevance",
        year_min: Annotated[int | None, Field(description="Start year filter (e.g. 1700).")] = None,
        year_max: Annotated[int | None, Field(description="End year filter (e.g. 1750).")] = None,
        dedup: Annotated[bool, Field(description="Session deduplication. True compacts already-seen documents; False forces full results.")] = True,
        research_context: Annotated[str | None, Field(description="Brief summary of the user's research goal. Used for telemetry only.")] = None,
        ctx: Context | None = None,
    ) -> str:
        """Search AI-transcribed text in digitised historical documents.

        This tool searches only transcribed text (not metadata).
        For metadata search, use search_metadata instead.
        """
        validation_error = _validate_search_input(keyword, offset, year_min, year_max, sort, limit)
        if validation_error:
            return validation_error

        if research_context:
            logger.info("MCP Tool: search_transcribed | context: %s", research_context)
        logger.info("MCP Tool: search_transcribed called with keyword='%s', offset=%d", keyword, offset)

        try:
            logger.debug("Initializing search operations...")
            search_operations = SearchOperations(http_client=default_http_client)
            formatter = PlainTextFormatter()

            logger.info("Executing transcribed text search for '%s'...", keyword)
            session_id = ctx.session_id if ctx is not None else None
            search_result = await search_operations.search(
                keyword=keyword,
                transcribed_only=True,  # Always search transcribed text
                only_digitised=True,  # Transcriptions only exist for digitised materials
                offset=offset,
                limit=limit,
                max_snippets_per_record=max_snippets_per_record,
                sort=sort,
                year_min=year_min,
                year_max=year_max,
                research_context=research_context,
                session_id=session_id,
            )

            # Load session state for dedup
            seen: dict[str, list[int]] | None = None
            if dedup and ctx is not None:
                seen = await ctx.get_state("seen_search") or {}
                logger.info("[search_transcribed] Dedup state loaded: %d documents previously seen", len(seen))

            logger.info("Formatting %d search results...", len(search_result.items))
            formatted_results = formatter.format_search_results(
                search_result,
                maximum_documents_to_display=limit,
                seen_pages=seen,
            )

            # Update session state with only the documents actually scanned by the formatter
            if dedup and ctx is not None:
                updated = _update_seen_search_state(seen or {}, search_result, max_displayed=formatter.items_scanned)
                await ctx.set_state("seen_search", updated)
                logger.info("[search_transcribed] Dedup state saved: %d documents now tracked", len(updated))

            formatted_results = _apply_token_limit_if_needed(formatted_results, max_response_tokens)
            formatted_results = _append_pagination_info_if_needed(formatted_results, search_result, offset, limit)

            logger.info("✓ Search completed successfully, returning results")
            return formatted_results

        except Exception as e:
            logger.error("✗ MCP search_transcribed failed: %s: %s", type(e).__name__, e, exc_info=True)
            mark_span_error(f"Search failed: {e!s}")
            formatter = PlainTextFormatter()
            return formatter.format_error_message(
                f"Search failed: {e!s}",
                error_suggestions=[
                    "Try a simpler search term",
                    "Check if the service is available",
                    "Reduce limit",
                    "Check Hugging Face logs for timeout details",
                ],
            )

    @mcp.tool(
        name="metadata",
        version="1.0",
        timeout=30.0,
        tags={"search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search document metadata (titles, names, places, descriptions) across the Swedish National Archives catalog. "
            "Covers 2M+ records when only_digitised=False, including non-digitised materials. "
            "Use the dedicated name parameter for person searches and place parameter for place searches — these can be combined with keyword.\n"
            "Does NOT search transcribed page text — use search_transcribed for that. "
            "Same Solr syntax as search_transcribed. Session dedup: re-calling returns stubs for already-seen documents.\n"
            "Important: name and place filter a dedicated metadata field that is sparsely populated. "
            "Most person/place matches are NOT digitised, so set only_digitised=False when using name or place to avoid empty results."
        ),
    )
    async def search_metadata(
        keyword: Annotated[str, Field(description="Free-text search across all metadata fields. Supports Solr syntax (wildcards, fuzzy, Boolean).")],
        offset: Annotated[int, Field(description="Pagination start position. Use 0 for first page, then 50, 100, etc.")],
        only_digitised: Annotated[bool, Field(description="True = digitised materials only. False = all 2M+ records including non-digitised.")] = True,
        limit: Annotated[int, Field(description="Maximum documents to return per query.")] = 25,
        max_response_tokens: Annotated[int, Field(description="Maximum tokens in response.", ge=1000)] = 15000,
        sort: Annotated[str, Field(description="Sort order: 'relevance', 'timeAsc', 'timeDesc', 'alphaAsc', 'alphaDesc'.")] = "relevance",
        year_min: Annotated[int | None, Field(description="Start year filter (e.g. 1700).")] = None,
        year_max: Annotated[int | None, Field(description="End year filter (e.g. 1750).")] = None,
        name: Annotated[
            str | None,
            Field(
                description="Person name search in dedicated name field (e.g. 'Nobel', 'Linné'). Combinable with keyword and place. Most name matches are non-digitised — set only_digitised=False."
            ),
        ] = None,
        place: Annotated[
            str | None,
            Field(
                description="Place name search in dedicated place field (e.g. 'Stockholm', 'Göteborg'). Combinable with keyword and name. Most place matches are non-digitised — set only_digitised=False."
            ),
        ] = None,
        dedup: Annotated[bool, Field(description="Session deduplication. True compacts already-seen documents; False forces full results.")] = True,
        research_context: Annotated[str | None, Field(description="Brief summary of the user's research goal. Used for telemetry only.")] = None,
        ctx: Context | None = None,
    ) -> str:
        """Search document metadata (titles, names, places, provenance).

        This tool searches metadata fields, not transcribed text.
        For transcription search, use search_transcribed instead.
        """
        validation_error = _validate_search_input(keyword, offset, year_min, year_max, sort, limit)
        if validation_error:
            return validation_error

        if research_context:
            logger.info("MCP Tool: search_metadata | context: %s", research_context)
        material_scope = "digitised materials" if only_digitised else "all materials (2M+ records)"
        logger.info("MCP Tool: search_metadata called with keyword='%s', offset=%d, scope=%s", keyword, offset, material_scope)

        try:
            logger.debug("Initializing search operations...")
            search_operations = SearchOperations(http_client=default_http_client)
            formatter = PlainTextFormatter()

            logger.info("Executing metadata search for '%s' in %s...", keyword, material_scope)
            session_id = ctx.session_id if ctx is not None else None
            search_result = await search_operations.search(
                keyword=keyword,
                transcribed_only=False,  # Search metadata fields
                only_digitised=only_digitised,
                offset=offset,
                limit=limit,
                max_snippets_per_record=None,  # Metadata search doesn't have snippets
                sort=sort,
                year_min=year_min,
                year_max=year_max,
                name=name,
                place=place,
                research_context=research_context,
                session_id=session_id,
            )

            # Load session state for dedup
            seen: dict[str, list[int]] | None = None
            if dedup and ctx is not None:
                seen = await ctx.get_state("seen_search") or {}
                logger.info("[search_metadata] Dedup state loaded: %d documents previously seen", len(seen))

            logger.info("Formatting %d search results...", len(search_result.items))
            formatted_results = formatter.format_search_results(
                search_result,
                maximum_documents_to_display=limit,
                seen_pages=seen,
            )

            # Update session state with only the documents actually scanned by the formatter
            if dedup and ctx is not None:
                updated = _update_seen_search_state(seen or {}, search_result, max_displayed=formatter.items_scanned)
                await ctx.set_state("seen_search", updated)
                logger.info("[search_metadata] Dedup state saved: %d documents now tracked", len(updated))

            formatted_results = _apply_token_limit_if_needed(formatted_results, max_response_tokens)
            formatted_results = _append_pagination_info_if_needed(formatted_results, search_result, offset, limit)

            logger.info("✓ Metadata search completed successfully, returning results")
            return formatted_results

        except Exception as e:
            logger.error("✗ MCP search_metadata failed: %s: %s", type(e).__name__, e, exc_info=True)
            mark_span_error(f"Metadata search failed: {e!s}")
            formatter = PlainTextFormatter()
            return formatter.format_error_message(
                f"Metadata search failed: {e!s}",
                error_suggestions=[
                    "Try a simpler search term",
                    "Check if the service is available",
                    "Reduce limit",
                    "Try with only_digitised=True for faster results",
                ],
            )


def _apply_token_limit_if_needed(formatted_results, max_response_tokens) -> str:
    """Apply token limit to the formatted results if needed."""
    estimated_tokens = len(formatted_results) // 4
    if estimated_tokens > max_response_tokens:
        return formatted_results[: max_response_tokens * 4] + "\n\n[Response truncated due to size limits]"
    return formatted_results


def _extract_unique_documents(search_hits) -> set[str]:
    """Extract unique document identifiers from hits."""
    unique_documents = set()
    for hit in search_hits:
        document_id = hit.metadata.reference_code or hit.id
        unique_documents.add(document_id)
    return unique_documents


def _calculate_pagination_metadata(unique_documents, search_hits, total_hits, offset, limit) -> dict[str, object]:
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


def _get_pagination_info(search_hits, total_hit_count, pagination_offset, result_limit) -> dict[str, object]:
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


def _append_pagination_info_if_needed(formatted_results, search_result, offset, limit) -> str:
    """Append pagination information to results if there are more results available."""
    pagination_info = _get_pagination_info(search_result.items, search_result.response.total_hits, offset, limit)

    if pagination_info["has_more"]:
        formatted_results += f"\n\n📊 **Pagination**: Showing documents {pagination_info['document_range_start']}-{pagination_info['document_range_end']}"
        formatted_results += f"\n💡 Use `offset={pagination_info['next_offset']}` to see the next {limit} documents"

    return formatted_results


def _update_seen_search_state(seen: dict[str, list[int]], search_result, max_displayed: int) -> dict[str, list[int]]:
    """Merge page numbers from search results into the seen-state dict.

    Only tracks documents that were actually displayed (up to max_displayed),
    not all documents returned by the API. This prevents marking unseen
    documents as "seen" when the API returns more items than are shown.

    For each document in the result, extracts page numbers from snippet page IDs
    and merges them into the existing seen set for that reference code.
    Documents without snippets (metadata-only) are recorded with an empty list.
    """
    for document in search_result.items[:max_displayed]:
        ref_code = document.metadata.reference_code or document.id
        existing = set(seen.get(ref_code, []))

        if document.transcribed_text and document.transcribed_text.snippets:
            for snippet in document.transcribed_text.snippets:
                for page in snippet.pages:
                    existing.add(page_id_to_number(page.id))
        # Store as sorted list (JSON-serializable)
        seen[ref_code] = sorted(existing)

    return seen

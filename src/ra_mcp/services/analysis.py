"""
Analysis functions for search results.
"""

from typing import Dict, List, Optional, Union

from ..models import SearchHit, SearchOperation


def group_hits_by_document(search_hits: List[SearchHit]) -> Dict[str, List[SearchHit]]:
    """Group search hits by document (reference code or PID).

    Args:
        search_hits: List of search hits to group

    Returns:
        Dictionary mapping document identifiers to their hits
    """
    document_grouped_hits = {}

    for hit in search_hits:
        document_identifier = hit.reference_code or hit.pid

        if document_identifier not in document_grouped_hits:
            document_grouped_hits[document_identifier] = []

        document_grouped_hits[document_identifier].append(hit)

    return document_grouped_hits


def get_pagination_info(
    search_hits: List[SearchHit],
    total_hit_count: int,
    pagination_offset: int,
    result_limit: int,
) -> Dict[str, Union[int, bool, Optional[int]]]:
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


def _extract_unique_documents(search_hits: List[SearchHit]) -> set:
    """Extract unique document identifiers from hits."""
    unique_documents = set()

    for hit in search_hits:
        document_id = hit.reference_code or hit.pid
        unique_documents.add(document_id)

    return unique_documents


def _calculate_pagination_metadata(
    unique_documents: set,
    search_hits: List[SearchHit],
    total_hits: int,
    offset: int,
    limit: int,
) -> Dict[str, Union[int, bool, Optional[int]]]:
    """Calculate pagination metadata."""
    has_additional_results = len(unique_documents) == limit and total_hits > len(
        search_hits
    )

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


def extract_search_summary(
    search_operation: SearchOperation,
) -> Dict[str, Union[str, int, bool, Dict[str, List[SearchHit]]]]:
    """Extract summary information from a search operation.

    Args:
        search_operation: Search operation to summarize

    Returns:
        Dictionary containing search summary
    """
    grouped_by_document = group_hits_by_document(search_operation.hits)

    search_summary = _build_search_summary(search_operation, grouped_by_document)

    return search_summary


def _build_search_summary(
    search_operation: SearchOperation, document_grouped_hits: Dict[str, List[SearchHit]]
) -> Dict[str, Union[str, int, bool, Dict[str, List[SearchHit]]]]:
    """Build summary dictionary from search operation."""
    return {
        "keyword": search_operation.keyword,
        "total_hits": search_operation.total_hits,
        "page_hits_returned": len(search_operation.hits),
        "documents_returned": len(document_grouped_hits),
        "enriched": search_operation.enriched,
        "offset": search_operation.offset,
        "grouped_hits": document_grouped_hits,
    }

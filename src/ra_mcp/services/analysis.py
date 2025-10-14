"""
Analysis functions for search results.
"""

from typing import Dict, List

from ..models import SearchHit, SearchResult, SearchSummary


def _group_hits_by_document(search_hits: List[SearchHit]) -> Dict[str, List[SearchHit]]:
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


def extract_search_summary(
    search_result: SearchResult,
) -> SearchSummary:
    """Extract summary information from a search operation.

    Args:
        search_result: Search operation to summarize

    Returns:
        Dictionary containing search summary
    """
    grouped_by_document = _group_hits_by_document(search_result.hits)

    search_summary = _build_search_summary(search_result, grouped_by_document)

    return search_summary


def _build_search_summary(search_result: SearchResult, document_grouped_hits: Dict[str, List[SearchHit]]) -> SearchSummary:
    """Build summary from search operation."""
    return SearchSummary(
        keyword=search_result.keyword,
        total_hits=search_result.total_hits,
        page_hits_returned=len(search_result.hits),
        documents_returned=len(document_grouped_hits),
        enriched=search_result.enriched,
        offset=search_result.offset,
        grouped_hits=document_grouped_hits,
    )

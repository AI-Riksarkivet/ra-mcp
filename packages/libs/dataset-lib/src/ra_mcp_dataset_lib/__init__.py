"""Shared LanceDB spine for the ra-mcp dataset libraries."""

from ra_mcp_dataset_lib.search import (
    MAX_TOTAL_COUNT,
    SearchResult,
    any_of,
    at_least,
    at_most,
    build_fts_index,
    build_scalar_indexes,
    combine,
    equals,
    format_results,
    get_lancedb,
    lancedb_fts_search,
    require_keyword,
    require_ordered_range,
    text_contains,
)


__all__ = [
    "MAX_TOTAL_COUNT",
    "SearchResult",
    "any_of",
    "at_least",
    "at_most",
    "build_fts_index",
    "build_scalar_indexes",
    "combine",
    "equals",
    "format_results",
    "get_lancedb",
    "lancedb_fts_search",
    "require_keyword",
    "require_ordered_range",
    "text_contains",
]

"""Shared LanceDB spine for the ra-mcp dataset libraries."""

from ra_mcp_dataset_lib.search import (
    MAX_TOTAL_COUNT,
    SearchResult,
    any_of,
    at_least,
    at_most,
    build_fts_index,
    combine,
    equals,
    get_lancedb,
    lancedb_fts_search,
    text_contains,
)


__all__ = [
    "MAX_TOTAL_COUNT",
    "SearchResult",
    "any_of",
    "at_least",
    "at_most",
    "build_fts_index",
    "combine",
    "equals",
    "get_lancedb",
    "lancedb_fts_search",
    "text_contains",
]

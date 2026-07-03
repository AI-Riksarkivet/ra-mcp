"""Shared LanceDB spine for the ra-mcp dataset libraries."""

from ra_mcp_dataset_lib.search import (
    MAX_TOTAL_COUNT,
    SearchResult,
    build_fts_index,
    get_lancedb,
    lancedb_fts_search,
)


__all__ = [
    "MAX_TOTAL_COUNT",
    "SearchResult",
    "build_fts_index",
    "get_lancedb",
    "lancedb_fts_search",
]

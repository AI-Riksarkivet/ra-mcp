"""
RA-MCP Search: Search domain for Riksarkivet.

Provides search client, operations, and models for searching transcribed documents.
"""

__version__ = "0.3.0"

from .models import RecordsResponse, SearchRecord, SearchResult
from .search_client import SearchClient
from .search_operations import SearchOperations


__all__ = [
    "RecordsResponse",
    "SearchClient",
    "SearchOperations",
    "SearchRecord",
    "SearchResult",
]

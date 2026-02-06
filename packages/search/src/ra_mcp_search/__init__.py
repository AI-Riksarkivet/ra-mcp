"""
RA-MCP Search: Search domain for Riksarkivet.

Provides search client, operations, and models for searching transcribed documents.
"""

__version__ = "0.2.13"

from .clients import SearchAPI
from .operations import SearchOperations
from .models import SearchResult, SearchRecord, RecordsResponse

__all__ = [
    "SearchAPI",
    "SearchOperations",
    "SearchResult",
    "SearchRecord",
    "RecordsResponse",
]

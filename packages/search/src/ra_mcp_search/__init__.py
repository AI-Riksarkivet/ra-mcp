"""
RA-MCP Search: Search domain for Riksarkivet.

Provides search client and operations for searching transcribed documents.
Models are imported from ra_mcp_core.
"""

__version__ = "0.2.7"

from .clients import SearchAPI
from .operations import SearchOperations

# Re-export models from core for convenience
from ra_mcp_core.models import SearchResult, SearchRecord, RecordsResponse

__all__ = [
    "SearchAPI",
    "SearchOperations",
    "SearchResult",
    "SearchRecord",
    "RecordsResponse",
]

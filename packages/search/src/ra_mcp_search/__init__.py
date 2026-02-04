"""
RA-MCP Search: Search operations for Riksarkivet.

Provides shared business logic (operations) for search and browse functionality
used by both CLI and MCP tool packages.
"""

__version__ = "0.2.7"

from .operations import SearchOperations, BrowseOperations

__all__ = [
    "SearchOperations",
    "BrowseOperations",
]

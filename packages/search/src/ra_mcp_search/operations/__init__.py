"""
Operations for search and browse functionality.

Provides business logic for executing searches and browsing documents.
"""

from .search_operations import SearchOperations
from .browse_operations import BrowseOperations

__all__ = [
    "SearchOperations",
    "BrowseOperations",
]

"""
RA-MCP Search: Search and browse MCP tools for Riksarkivet.

Provides MCP tools for searching and browsing transcribed historical documents
from the Swedish National Archives.
"""

__version__ = "0.2.7"

from .mcp import search_mcp
from .operations import SearchOperations, BrowseOperations

__all__ = [
    "search_mcp",
    "SearchOperations",
    "BrowseOperations",
]

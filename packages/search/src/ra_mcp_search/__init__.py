"""
RA-MCP Search: Search operations and formatters for Riksarkivet.

Provides shared business logic and formatting for search and browse functionality
used by both CLI and MCP tool packages.
"""

__version__ = "0.2.7"

from .operations import SearchOperations, BrowseOperations
from .formatters import PlainTextFormatter, RichConsoleFormatter

__all__ = [
    "SearchOperations",
    "BrowseOperations",
    "PlainTextFormatter",
    "RichConsoleFormatter",
]

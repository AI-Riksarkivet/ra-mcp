"""
Formatters for search and browse results.

Provides formatters for different output interfaces (CLI and MCP)
and display orchestration services.
"""

from .base_formatter import BaseFormatter
from .rich_formatter import RichConsoleFormatter
from .plain_formatter import PlainTextFormatter
from .search_display import SearchDisplayService
from .browse_display import BrowseDisplayService
from . import utils

__all__ = [
    "BaseFormatter",
    "RichConsoleFormatter",
    "PlainTextFormatter",
    "SearchDisplayService",
    "BrowseDisplayService",
    "utils",
]

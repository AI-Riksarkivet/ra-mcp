"""
Formatters for search and browse results.

Provides formatters for different output interfaces (CLI and MCP).
"""

from .rich_formatter import RichConsoleFormatter
from .plain_formatter import PlainTextFormatter
from . import utils

__all__ = [
    "RichConsoleFormatter",
    "PlainTextFormatter",
    "utils",
]

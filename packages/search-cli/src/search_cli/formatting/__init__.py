"""Formatting utilities for CLI output."""

from .formatter import RichConsoleFormatter
from .utils import (
    trim_page_number,
    trim_page_numbers,
    truncate_text,
    format_example_browse_command,
)

__all__ = [
    "RichConsoleFormatter",
    "trim_page_number",
    "trim_page_numbers",
    "truncate_text",
    "format_example_browse_command",
]

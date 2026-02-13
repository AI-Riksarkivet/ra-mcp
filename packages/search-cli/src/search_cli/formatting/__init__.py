"""Formatting utilities for CLI output."""

from .formatter import RichConsoleFormatter
from .utils import (
    format_example_browse_command,
    trim_page_number,
    trim_page_numbers,
    truncate_text,
)


__all__ = [
    "RichConsoleFormatter",
    "format_example_browse_command",
    "trim_page_number",
    "trim_page_numbers",
    "truncate_text",
]

"""
Base formatter abstract class for different output formats.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseFormatter(ABC):
    @abstractmethod
    def format_text(self, text_content: str, style_name: str = "") -> str:
        pass

    @abstractmethod
    def format_table(self, column_headers: List[str], table_rows: List[List[str]], table_title: str = "") -> str:
        pass

    @abstractmethod
    def format_panel(self, panel_content: str, panel_title: str = "", panel_border_style: str = "") -> str:
        pass

    @abstractmethod
    def highlight_search_keyword(self, text_content: str, search_keyword: str) -> str:
        pass


def format_error_message(error_message: str, error_suggestions: Optional[List[str]] = None) -> str:
    formatted_lines = []
    formatted_lines.append(f"⚠️ **Error**: {error_message}")

    if error_suggestions:
        formatted_lines.append("\n**Suggestions**:")
        for suggestion_text in error_suggestions:
            formatted_lines.append(f"- {suggestion_text}")

    return "\n".join(formatted_lines)
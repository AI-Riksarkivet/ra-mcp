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
    def format_table(
        self,
        column_headers: List[str],
        table_rows: List[List[str]],
        table_title: str = "",
    ) -> str:
        pass

    @abstractmethod
    def format_panel(self, panel_content: str, panel_title: str = "", panel_border_style: str = "") -> str:
        pass

    @abstractmethod
    def highlight_search_keyword(self, text_content: str, search_keyword: str) -> str:
        pass

    @abstractmethod
    def format_no_results_message(self, search_result) -> str:
        """
        Generate appropriate message when no results are found.

        Args:
            search_result: SearchResult containing keyword, offset, and total_hits

        Returns:
            Formatted no results message
        """
        pass

    @abstractmethod
    def format_search_results(self, search_result, max_display: int) -> str:
        """
        Format search results for display.

        Args:
            search_result: SearchResult containing hits and metadata
            max_display: Maximum number of documents to display

        Returns:
            Formatted search results (str for base type, implementations may return other types)
        """
        pass

    @abstractmethod
    def format_browse_results(
        self,
        browse_result,
        highlight_term=None,
        show_links: bool = False,
        show_success_message: bool = True,
    ) -> str:
        """
        Format browse results for display.

        Args:
            browse_result: BrowseResult containing page contexts and metadata
            highlight_term: Optional term to highlight in text
            show_links: Whether to show ALTO/Image/Bildvisning links
            show_success_message: Whether to show success message

        Returns:
            Formatted browse results (str for base type, implementations may return other types)
        """
        pass


def format_error_message(error_message: str, error_suggestions: Optional[List[str]] = None) -> str:
    formatted_lines = []
    formatted_lines.append(f"⚠️ **Error**: {error_message}")

    if error_suggestions:
        formatted_lines.append("\n**Suggestions**:")
        for suggestion_text in error_suggestions:
            formatted_lines.append(f"- {suggestion_text}")

    return "\n".join(formatted_lines)

"""
Plain text formatter for MCP/LLM output without any Rich markup.
"""

import re
from typing import List

from .base_formatter import BaseFormatter


class PlainTextFormatter(BaseFormatter):
    """Formatter that produces plain text without any Rich markup."""

    def format_text(self, text_content: str, style_name: str = "") -> str:
        """Return plain text without any styling."""
        return text_content

    def format_table(
        self,
        column_headers: List[str],
        table_rows: List[List[str]],
        table_title: str = "",
    ) -> str:
        """
        Create a plain text table without borders.

        Args:
            column_headers: List of column headers
            table_rows: List of row data
            table_title: Optional table title

        Returns:
            Plain text formatted table
        """
        formatted_lines = []
        if table_title:
            formatted_lines.append(table_title)
            formatted_lines.append("")

        # Calculate column widths
        all_table_rows = [column_headers] + table_rows
        column_widths = [
            max(len(str(row[column_index])) for row in all_table_rows)
            for column_index in range(len(column_headers))
        ]

        # Format header
        formatted_header = " | ".join(
            column_headers[column_index].ljust(column_widths[column_index])
            for column_index in range(len(column_headers))
        )
        formatted_lines.append(formatted_header)

        # Add simple separator
        formatted_lines.append("-" * len(formatted_header))

        # Format rows
        for data_row in table_rows:
            formatted_row = " | ".join(
                str(data_row[column_index]).ljust(column_widths[column_index])
                for column_index in range(len(data_row))
            )
            formatted_lines.append(formatted_row)

        return "\n".join(formatted_lines)

    def format_panel(
        self, panel_content: str, panel_title: str = "", panel_border_style: str = ""
    ) -> str:
        """
        Format content as plain text without panels or borders.

        Args:
            panel_content: Content to display
            panel_title: Optional title
            panel_border_style: Ignored in plain text mode

        Returns:
            Plain text formatted content
        """
        formatted_lines = []
        if panel_title:
            formatted_lines.append(panel_title)
            formatted_lines.append("")
        formatted_lines.append(panel_content)
        return "\n".join(formatted_lines)

    def highlight_search_keyword(self, text_content: str, search_keyword: str) -> str:
        """
        Highlight search keywords using markdown-style bold.

        Args:
            text_content: Text to search in
            search_keyword: Keyword to highlight

        Returns:
            Text with keywords wrapped in **bold**
        """
        if not search_keyword:
            return text_content
        keyword_pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
        return keyword_pattern.sub(
            lambda match: f"**{match.group()}**", text_content
        )
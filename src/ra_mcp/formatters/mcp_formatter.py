"""
MCP/LLM formatter for plain text output with markdown support.
"""

import re
from typing import List

from .base_formatter import BaseFormatter


class MCPFormatter(BaseFormatter):
    def format_text(self, text_content: str, style_name: str = "") -> str:
        return text_content

    def format_table(
        self,
        column_headers: List[str],
        table_rows: List[List[str]],
        table_title: str = "",
    ) -> str:
        formatted_lines = []
        if table_title:
            formatted_lines.append(f"# {table_title}")
            formatted_lines.append("")

        all_table_rows = [column_headers] + table_rows
        column_widths = [
            max(len(str(row[column_index])) for row in all_table_rows)
            for column_index in range(len(column_headers))
        ]

        formatted_header = " | ".join(
            column_headers[column_index].ljust(column_widths[column_index])
            for column_index in range(len(column_headers))
        )
        formatted_lines.append(formatted_header)
        formatted_lines.append("-" * len(formatted_header))

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
        formatted_lines = []
        if panel_title:
            formatted_lines.append(f"## {panel_title}")
            formatted_lines.append("")
        formatted_lines.append(panel_content)
        return "\n".join(formatted_lines)

    def highlight_search_keyword(self, text_content: str, search_keyword: str) -> str:
        if not search_keyword:
            return text_content
        keyword_pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
        return keyword_pattern.sub(lambda match: f"**{match.group()}**", text_content)

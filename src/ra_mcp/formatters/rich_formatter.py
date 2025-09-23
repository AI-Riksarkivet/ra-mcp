"""
Rich console formatter for CLI output.
"""

import re
from typing import List

from .base_formatter import BaseFormatter


class RichConsoleFormatter(BaseFormatter):
    def format_text(self, text_content: str, style_name: str = "") -> str:
        if style_name:
            return f"[{style_name}]{text_content}[/{style_name}]"
        return text_content

    def format_table(self, column_headers: List[str], table_rows: List[List[str]], table_title: str = "") -> str:
        return f"TABLE: {table_title}\nHeaders: {column_headers}\nRows: {len(table_rows)}"

    def format_panel(self, panel_content: str, panel_title: str = "", panel_border_style: str = "") -> str:
        return f"PANEL: {panel_title}\n{panel_content}"

    def highlight_search_keyword(self, text_content: str, search_keyword: str) -> str:
        if not search_keyword:
            return text_content
        keyword_pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
        return keyword_pattern.sub(lambda match: f"[bold yellow underline]{match.group()}[/bold yellow underline]", text_content)
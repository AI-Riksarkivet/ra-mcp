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
        column_widths = [max(len(str(row[column_index])) for row in all_table_rows) for column_index in range(len(column_headers))]

        # Format header
        formatted_header = " | ".join(column_headers[column_index].ljust(column_widths[column_index]) for column_index in range(len(column_headers)))
        formatted_lines.append(formatted_header)

        # Add simple separator
        formatted_lines.append("-" * len(formatted_header))

        # Format rows
        for data_row in table_rows:
            formatted_row = " | ".join(str(data_row[column_index]).ljust(column_widths[column_index]) for column_index in range(len(data_row)))
            formatted_lines.append(formatted_row)

        return "\n".join(formatted_lines)

    def format_panel(self, panel_content: str, panel_title: str = "", panel_border_style: str = "") -> str:
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
        The **text** markers from the API are already in the correct format.
        If no markers present, fallback to manual keyword highlighting.

        Args:
            text_content: Text to search in (may already contain **text** markers)
            search_keyword: Keyword to highlight

        Returns:
            Text with keywords wrapped in **bold**
        """
        if re.search(r"\*\*[^*]+\*\*", text_content):
            return text_content

        if not search_keyword:
            return text_content
        keyword_pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
        return keyword_pattern.sub(lambda match: f"**{match.group()}**", text_content)

    def format_no_results_message(self, search_result) -> str:
        """
        Generate appropriate message when no results are found.

        Args:
            search_result: SearchResult containing keyword, offset, and total_hits

        Returns:
            Formatted no results message
        """
        if search_result.offset > 0:
            return f"No more results found for '{search_result.keyword}' at offset {search_result.offset}. Total results: {search_result.total_hits}"
        return f"No results found for '{search_result.keyword}'. make sure to use \"\" "

    def format_search_results(self, search_result, maximum_documents_to_display: int = 20) -> str:
        """
        Format search results as plain text with emojis for MCP/LLM consumption.

        Args:
            search_result: SearchResult containing documents and metadata
            maximum_documents_to_display: Maximum number of documents to display

        Returns:
            Formatted plain text search results
        """
        if not search_result.items:
            return self.format_no_results_message(search_result)

        lines = []
        snippet_count = search_result.count_snippets()
        lines.append(f"Found {snippet_count} page-level hits across {len(search_result.items)} documents")
        lines.append("")

        for idx, document in enumerate(search_result.items[:maximum_documents_to_display]):
            if not document.transcribed_text or not document.transcribed_text.snippets:
                continue

            lines.append(f"📚 Document: {document.metadata.reference_code}")

            if document.metadata.archival_institution:
                institution = document.metadata.archival_institution[0].caption
                lines.append(f"🏛️  Institution: {institution}")

            if document.metadata.date:
                lines.append(f"📅 Date: {document.metadata.date}")

            title = document.get_title()
            title_display = title[:100] + "..." if len(title) > 100 else title
            lines.append(f"📄 Title: {title_display}")

            # Extract page numbers from snippets
            page_numbers = sorted(set(
                page.id
                for snippet in document.transcribed_text.snippets
                for page in snippet.pages
            ))
            trimmed_page_numbers = [page_num.lstrip("0") or "0" for page_num in page_numbers]

            snippet_count = len(document.transcribed_text.snippets)
            total_hits = document.get_total_hits()
            hit_label = "hit" if snippet_count == 1 else "hits"

            lines.append(f"📖 Pages with hits: {', '.join(trimmed_page_numbers)}")

            # Show total hits if available and different from shown count
            if total_hits > snippet_count:
                lines.append(f"💡 {snippet_count} {hit_label} shown ({total_hits} total)")
            else:
                lines.append(f"💡 {snippet_count} {hit_label} found")

            # Show first 3 snippets
            for snippet in document.transcribed_text.snippets[:3]:
                snippet_text = self.highlight_search_keyword(snippet.text, search_result.keyword)
                if snippet.pages:
                    page_id = snippet.pages[0].id
                    lines.append(f"   Page {page_id}: {snippet_text}")

            if len(document.transcribed_text.snippets) > 3:
                lines.append(f"   ...and {len(document.transcribed_text.snippets) - 3} more pages with hits")

            lines.append("")

        total_document_count = len(search_result.items)
        if total_document_count > maximum_documents_to_display:
            remaining_documents = total_document_count - maximum_documents_to_display
            lines.append(f"... and {remaining_documents} more documents")

        return "\n".join(lines)

    def format_browse_results(
        self,
        browse_result,
        highlight_term=None,
        show_links: bool = False,
        show_success_message: bool = True,
    ) -> str:
        """
        Format browse results as plain text with emojis for MCP/LLM consumption.

        Args:
            browse_result: BrowseResult containing page contexts and metadata
            highlight_term: Optional term to highlight in text
            show_links: Whether to show ALTO/Image/Bildvisning links
            show_success_message: Whether to show success message (ignored in plain text)

        Returns:
            Formatted plain text browse results
        """
        if not browse_result.contexts:
            return f"No page contexts found for {browse_result.reference_code}"

        lines = []
        lines.append(f"📚 Document: {browse_result.reference_code}")

        # Add rich metadata if available
        if browse_result.document_metadata:
            metadata = browse_result.document_metadata

            # Display title
            if metadata.title and metadata.title != "(No title)":
                lines.append(f"📋 Title: {metadata.title}")

            # Display date range
            if metadata.date:
                lines.append(f"📅 Date: {metadata.date}")

            # Display archival institution
            if metadata.archival_institution:
                institutions = metadata.archival_institution
                if institutions:
                    inst_names = [inst.get("caption", "") for inst in institutions]
                    lines.append(f"🏛️  Institution: {', '.join(inst_names)}")

            # Display hierarchy
            if metadata.hierarchy:
                hierarchy = metadata.hierarchy
                if hierarchy:
                    for i, level in enumerate(hierarchy):
                        caption = level.get("caption", "")
                        caption = caption.replace("\n", " ").strip()

                        if i == 0:
                            lines.append(f"📁 {caption}")
                        elif i == len(hierarchy) - 1:
                            indent = "  " * i
                            lines.append(f"{indent}└── 📄 {caption}")
                        else:
                            indent = "  " * i
                            lines.append(f"{indent}├── 📁 {caption}")

            # Display note if available
            if metadata.note:
                lines.append(f"📝 Note: {metadata.note}")

        lines.append(f"📖 Pages loaded: {len(browse_result.contexts)}")
        lines.append("")

        for context in browse_result.contexts:
            lines.append(f"📄 Page {context.page_number}")
            lines.append("─" * 40)

            display_text = context.full_text
            if highlight_term:
                display_text = self.highlight_search_keyword(display_text, highlight_term)

            lines.append(display_text)
            lines.append("")
            lines.append("🔗 Links:")
            lines.append(f"  📝 ALTO XML: {context.alto_url}")
            if context.image_url:
                lines.append(f"  🖼️  Image: {context.image_url}")
            if context.bildvisning_url:
                lines.append(f"  👁️  Bildvisning: {context.bildvisning_url}")

            lines.append("")

        return "\n".join(lines)

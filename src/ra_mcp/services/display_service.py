"""
Display service that works for both MCP and CLI contexts.
Combines all display logic with conditional formatting based on border visibility.
"""

from typing import Dict, List, Optional, Union, Any

from ..models import SearchResult, BrowseResult
from ..formatters import PlainTextFormatter
from . import analysis


class DisplayService:
    """Display service for both MCP and CLI contexts."""

    def __init__(self, formatter=None, show_border=None):
        """
        Initialize the display service.

        Args:
            formatter: Formatter instance to use (PlainTextFormatter or RichConsoleFormatter)
                      If None, defaults to PlainTextFormatter
            show_border: Whether to show borders/separators in output. If None, determines based on formatter type
        """
        self.formatter = formatter or PlainTextFormatter()
        # Determine border visibility - PlainTextFormatter (MCP mode) typically doesn't show borders
        self.show_border = show_border if show_border is not None else not isinstance(self.formatter, PlainTextFormatter)

    def format_search_results(
        self,
        search_operation: SearchResult,
        maximum_documents_to_display: int = 20,
        show_full_context: bool = False,
    ) -> Union[str, Any]:
        """Format search results using Rich table for CLI or plain text for MCP."""
        # For CLI mode without full context, use Rich table
        if self.show_border and not show_full_context and hasattr(self.formatter, "format_search_results_table"):
            return self.formatter.format_search_results_table(search_operation, maximum_documents_to_display)

        # For MCP mode or full context display, use string formatting
        if not search_operation.hits:
            return  self._generate_no_results_message()

        search_summary = analysis.extract_search_summary(search_operation)
        hits_grouped_by_document = search_summary.grouped_hits

        lines = []
        lines.append(f"Found {search_summary.page_hits_returned} page-level hits across {search_summary.documents_returned} documents")

        lines.append("")

        displayed_document_count = 0
        for reference_code, document_hits in hits_grouped_by_document.items():
            if displayed_document_count >= maximum_documents_to_display:
                break
            displayed_document_count += 1

            first_hit = document_hits[0]
            lines.append(f"📚 Document: {reference_code}")
            if first_hit.archival_institution:
                institution = first_hit.archival_institution[0].get("caption", "")
                if institution:
                    lines.append(f"🏛️  Institution: {institution}")

            if first_hit.date:
                lines.append(f"📅 Date: {first_hit.date}")

            title = first_hit.title[:100] + "..." if len(first_hit.title) > 100 else first_hit.title
            lines.append(f"📄 Title: {title}")

            page_numbers = sorted(set(hit.page_number for hit in document_hits))
            trimmed_page_numbers = [page_num.lstrip("0") or "0" for page_num in page_numbers]
            lines.append(f"📖 Pages with hits: {', '.join(trimmed_page_numbers)}")

            if show_full_context and search_operation.enriched:
                for hit in document_hits[:3]:
                    if hit.full_page_text:
                        is_search_hit = hit.snippet_text != "[Context page - no search hit]"
                        page_type = "SEARCH HIT" if is_search_hit else "context"

                        lines.append(f"\n   📄 Page {hit.page_number} ({page_type}):")

                        display_text = hit.full_page_text
                        if is_search_hit:
                            display_text = self.formatter.highlight_search_keyword(display_text, search_operation.keyword)

                        if len(display_text) > 500:
                            display_text = display_text[:500] + "..."

                        lines.append(f"   {display_text}")
            else:
                for hit in document_hits[:3]:
                    snippet = hit.snippet_text
                    snippet = self.formatter.highlight_search_keyword(snippet, search_operation.keyword)
                    lines.append(f"   Page {hit.page_number}: {snippet}")

            if len(document_hits) > 3:
                lines.append(f"   ...and {len(document_hits) - 3} more pages with hits")

            lines.append("")

        total_document_count = len(hits_grouped_by_document)
        if total_document_count > displayed_document_count:
            remaining_documents = total_document_count - displayed_document_count
            lines.append(f"... and {remaining_documents} more documents")

        return "\n".join(lines)



    def _generate_no_results_message(self,keyword, offset, total_hits):
        """Generate appropriate message when no results are found."""
        if offset > 0:
            return f"No more results found for '{keyword}' at offset {offset}. Total results: {total_hits}"
        return f"No results found for '{keyword}'. make sure to use \"\" "



    def format_browse_results(self, operation: BrowseResult, highlight_term: Optional[str] = None) -> Union[List[Any], str]:
        """Format browse results as Rich Panel objects for CLI or string for MCP."""
        # For CLI mode, use Rich panels
        if self.show_border and hasattr(self.formatter, "format_page_context_panel"):
            panels = []
            for context in operation.contexts:
                panel = self.formatter.format_page_context_panel(context, highlight_term)
                panels.append(panel)
            return panels

        # For MCP mode or fallback, use string formatting without borders
        if not operation.contexts:
            return f"No page contexts found for {operation.reference_code}"

        lines = []
        lines.append(f"📚 Document: {operation.reference_code}")

        # Add rich metadata if available (same as CLI mode)
        if operation.document_metadata:
            metadata = operation.document_metadata

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
                        # Replace newlines with spaces to keep hierarchy on single lines
                        caption = caption.replace("\n", " ").strip()

                        if i == 0:
                            # Root level
                            lines.append(f"📁 {caption}")
                        elif i == len(hierarchy) - 1:
                            # Last item
                            indent = "  " * i
                            lines.append(f"{indent}└── 📄 {caption}")
                        else:
                            # Middle items
                            indent = "  " * i
                            lines.append(f"{indent}├── 📁 {caption}")

            # Display note if available
            if metadata.note:
                lines.append(f"📝 Note: {metadata.note}")

        lines.append(f"📖 Pages loaded: {len(operation.contexts)}")
        lines.append("")

        for context in operation.contexts:
            lines.append(f"📄 Page {context.page_number}")

            # Only add separator line if showing borders
            if self.show_border:
                lines.append("─" * 40)

            display_text = context.full_text
            if highlight_term:
                display_text = self.formatter.highlight_search_keyword(display_text, highlight_term)

            lines.append(display_text)
            lines.append("")
            lines.append("🔗 Links:")
            lines.append(f"  📝 ALTO XML: {context.alto_url}")
            if context.image_url:
                lines.append(f"  🖼️  Image: {context.image_url}")
            if context.bildvisning_url:
                lines.append(f"  👁️  Bildvisning: {context.bildvisning_url}")

            lines.append("")

        # Return string for MCP (no borders), list for CLI fallback
        return "\n".join(lines) if not self.show_border else ["\n".join(lines)]

    def format_document_structure(self, collection_info: Dict[str, Union[str, List[Dict[str, str]]]]) -> str:
        """Format document structure information as string."""
        if not collection_info:
            return "No document structure information available"

        lines = []
        lines.append(f"📚 Collection: {collection_info.get('title', 'Unknown')}")
        lines.append(f"🔗 Collection URL: {collection_info.get('collection_url', '')}")
        lines.append("")

        manifests = collection_info.get("manifests", [])
        if manifests:
            lines.append(f"📖 Available manifests ({len(manifests)}):")
            for manifest in manifests:
                lines.append(f"  • {manifest.get('label', 'Untitled')} ({manifest.get('id', '')})")
                lines.append(f"    URL: {manifest.get('url', '')}")
        else:
            lines.append("No manifests found")

        return "\n".join(lines)

    def format_error_message(self, error_message: str, error_suggestions: Optional[List[str]] = None) -> str:
        """Format error messages as string."""
        formatted_lines = [f"❌ Error: {error_message}"]

        if error_suggestions:
            formatted_lines.append("")
            formatted_lines.append("💡 Suggestions:")
            for suggestion_text in error_suggestions:
                formatted_lines.append(f"  • {suggestion_text}")

        return "\n".join(formatted_lines)

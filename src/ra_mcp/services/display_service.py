"""
Unified display service that can format output for different interfaces.
This eliminates formatting code duplication between CLI and MCP tools.
"""

from typing import Dict, List, Optional, Union, Any

from ..models import SearchHit, SearchOperation, BrowseOperation
from . import analysis
from ..formatters import BaseFormatter


class DisplayService:
    def __init__(self, formatter: BaseFormatter):
        self.formatter = formatter

    def is_rich_formatter(self) -> bool:
        """Check if the formatter is a RichConsoleFormatter."""
        return hasattr(self.formatter, "format_search_results_table")

    def format_search_results(
        self,
        search_operation: SearchOperation,
        maximum_documents_to_display: int = 20,
        show_full_context: bool = False,
    ) -> Union[str, Any]:
        """
        Format search results. Returns Rich objects for RichConsoleFormatter,
        or formatted strings for other formatters.
        """
        # Use Rich-specific formatting if available
        if self.is_rich_formatter() and not show_full_context:
            return self.formatter.format_search_results_table(
                search_operation, maximum_documents_to_display
            )

        # Original string-based formatting for MCP and full context display
        if not search_operation.hits:
            return "No search hits found."

        search_summary = analysis.extract_search_summary(search_operation)
        hits_grouped_by_document = search_summary["grouped_hits"]

        lines = []
        lines.append(
            f"Found {search_summary['page_hits_returned']} page-level hits across {search_summary['documents_returned']} documents"
        )

        if not show_full_context:
            lines.append(
                "💡 Tips: Use --context to see full page transcriptions | Use 'browse' command to view specific reference codes"
            )

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

            title = (
                first_hit.title[:100] + "..."
                if len(first_hit.title) > 100
                else first_hit.title
            )
            lines.append(f"📄 Title: {title}")

            page_numbers = sorted(set(hit.page_number for hit in document_hits))
            trimmed_page_numbers = [
                page_num.lstrip("0") or "0" for page_num in page_numbers
            ]
            lines.append(f"📖 Pages with hits: {', '.join(trimmed_page_numbers)}")

            if show_full_context and search_operation.enriched:
                for hit in document_hits[:3]:
                    if hit.full_page_text:
                        is_search_hit = (
                            hit.snippet_text != "[Context page - no search hit]"
                        )
                        page_type = "SEARCH HIT" if is_search_hit else "context"

                        lines.append(f"\n   📄 Page {hit.page_number} ({page_type}):")

                        display_text = hit.full_page_text
                        if is_search_hit:
                            display_text = self.formatter.highlight_search_keyword(
                                display_text, search_operation.keyword
                            )

                        if len(display_text) > 500:
                            display_text = display_text[:500] + "..."

                        lines.append(f"   {display_text}")
            else:
                for hit in document_hits[:3]:
                    snippet = (
                        hit.snippet_text[:150] + "..."
                        if len(hit.snippet_text) > 150
                        else hit.snippet_text
                    )
                    snippet = self.formatter.highlight_search_keyword(
                        snippet, search_operation.keyword
                    )
                    lines.append(f"   Page {hit.page_number}: {snippet}")

            if len(document_hits) > 3:
                lines.append(f"   ...and {len(document_hits) - 3} more pages with hits")

            lines.append("")

        total_document_count = len(hits_grouped_by_document)
        if total_document_count > displayed_document_count:
            remaining_documents = total_document_count - displayed_document_count
            lines.append(f"... and {remaining_documents} more documents")

        return "\n".join(lines)

    def format_browse_results(
        self, operation: BrowseOperation, highlight_term: Optional[str] = None
    ) -> Union[str, List[Any]]:
        """
        Format browse results. Returns Rich Panel objects for RichConsoleFormatter,
        or formatted strings for other formatters.
        """
        # Use Rich-specific formatting if available
        if self.is_rich_formatter() and hasattr(
            self.formatter, "format_page_context_panel"
        ):
            panels = []
            for context in operation.contexts:
                panel = self.formatter.format_page_context_panel(
                    context, highlight_term
                )
                panels.append(panel)
            return panels

        # Original string-based formatting for MCP
        if not operation.contexts:
            return f"No page contexts found for {operation.reference_code}"

        lines = []
        lines.append(f"📚 Document: {operation.reference_code}")
        lines.append(f"📖 Pages loaded: {len(operation.contexts)}")
        lines.append("")

        for context in operation.contexts:
            lines.append(f"📄 Page {context.page_number}")
            lines.append("─" * 40)

            # Format the text content
            display_text = context.full_text
            if highlight_term:
                display_text = self.formatter.highlight_search_keyword(
                    display_text, highlight_term
                )

            lines.append(display_text)
            lines.append("")

            # Add links
            lines.append("🔗 Links:")
            lines.append(f"  📝 ALTO XML: {context.alto_url}")
            if context.image_url:
                lines.append(f"  🖼️  Image: {context.image_url}")
            if context.bildvisning_url:
                lines.append(f"  👁️  Bildvisning: {context.bildvisning_url}")

            lines.append("")

        return "\n".join(lines)

    def format_show_pages_results(
        self,
        search_op: SearchOperation,
        enriched_hits: List[SearchHit],
        no_grouping: bool = False,
    ) -> Union[str, List[Any]]:
        """
        Format show-pages results (search + context).
        Returns Rich objects for RichConsoleFormatter, or strings for other formatters.
        """
        if not enriched_hits:
            return f"No pages found containing '{search_op.keyword}'"

        # Use Rich-specific formatting if available
        if self.is_rich_formatter() and hasattr(
            self.formatter, "format_document_panel"
        ):
            if no_grouping:
                # Return individual page panels
                panels = []
                for hit in enriched_hits:
                    if hit.full_page_text:
                        # Create a single-hit panel
                        panel = self.formatter.format_document_panel(
                            hit.reference_code, [hit], search_op.keyword
                        )
                        panels.append(panel)
                return panels
            else:
                # Group by document and return document panels
                grouped = analysis.group_hits_by_document(enriched_hits)
                panels = []
                for doc_ref, doc_hits in grouped.items():
                    panel = self.formatter.format_document_panel(
                        doc_ref, doc_hits, search_op.keyword
                    )
                    panels.append(panel)
                return panels

        # Original string-based formatting for MCP
        lines = []
        lines.append(f"🔍 Search results for '{search_op.keyword}':")
        lines.append(
            f"Found {len(search_op.hits)} initial hits, showing {len(enriched_hits)} pages with context"
        )
        lines.append("")

        if no_grouping:
            # Show individual pages
            for hit in enriched_hits:
                if hit.full_page_text:
                    is_search_hit = hit.snippet_text != "[Context page - no search hit]"
                    page_type = "🎯 SEARCH HIT" if is_search_hit else "📄 context"

                    lines.append(
                        f"{page_type}: {hit.reference_code} - Page {hit.page_number}"
                    )
                    lines.append("─" * 60)

                    display_text = hit.full_page_text
                    if is_search_hit:
                        display_text = self.formatter.highlight_search_keyword(
                            display_text, search_op.keyword
                        )

                    lines.append(display_text)
                    lines.append("")
        else:
            # Group by document
            grouped = analysis.group_hits_by_document(enriched_hits)

            for doc_ref, doc_hits in grouped.items():
                # Sort by page number
                doc_hits.sort(
                    key=lambda h: int(h.page_number) if h.page_number.isdigit() else 0
                )

                lines.append(f"📚 Document: {doc_ref} ({len(doc_hits)} pages)")
                lines.append("=" * 60)

                # Add document metadata
                first_hit = doc_hits[0]
                if first_hit.title:
                    lines.append(f"📄 Title: {first_hit.title}")
                if first_hit.date:
                    lines.append(f"📅 Date: {first_hit.date}")

                lines.append("")

                # Show each page
                for hit in doc_hits:
                    is_search_hit = hit.snippet_text != "[Context page - no search hit]"
                    page_marker = "🎯" if is_search_hit else "📄"
                    page_type = "SEARCH HIT" if is_search_hit else "context"

                    lines.append(f"{page_marker} Page {hit.page_number} ({page_type})")
                    lines.append("─" * 40)

                    if hit.full_page_text:
                        display_text = hit.full_page_text
                        if is_search_hit:
                            display_text = self.formatter.highlight_search_keyword(
                                display_text, search_op.keyword
                            )
                        lines.append(display_text)
                    else:
                        lines.append("No text content available")

                    lines.append("")

                lines.append("")

        return "\n".join(lines)

    def format_document_structure(
        self, collection_info: Dict[str, Union[str, List[Dict[str, str]]]]
    ) -> str:
        """Format document structure information."""
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
                lines.append(
                    f"  • {manifest.get('label', 'Untitled')} ({manifest.get('id', '')})"
                )
                lines.append(f"    URL: {manifest.get('url', '')}")
        else:
            lines.append("No manifests found")

        return "\n".join(lines)

    def format_error_message(
        self, error_message: str, error_suggestions: List[str] = None
    ) -> str:
        formatted_lines = [f"❌ Error: {error_message}"]

        if error_suggestions:
            formatted_lines.append("")
            formatted_lines.append("💡 Suggestions:")
            for suggestion_text in error_suggestions:
                formatted_lines.append(f"  • {suggestion_text}")

        return "\n".join(formatted_lines)

    def get_search_summary(self, search_operation: SearchOperation) -> Dict[str, Any]:
        """Get search summary for display."""
        return analysis.extract_search_summary(search_operation)

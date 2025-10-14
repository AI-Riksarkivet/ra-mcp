"""
Search display service for formatting search results.
"""

from typing import Union, Any, List
from .base_display_service import BaseDisplayService
from ..models import SearchResult


class SearchDisplayService(BaseDisplayService):
    """Display service specifically for search operations."""

    def format_search_results(
        self,
        search_result: SearchResult,
        maximum_documents_to_display: int = 20,
    ) -> Union[str, Any]:
        """Format search results using Rich table for CLI or plain text for MCP."""

        # For CLI mode, use Rich table
        if self.show_border and hasattr(self.formatter, "format_search_results_table"):
            return self.formatter.format_search_results_table(search_result, maximum_documents_to_display)

        if not search_result.hits:
            return self._generate_no_results_message(search_result)

        search_summary = search_result.extract_summary()
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

            for hit in document_hits[:3]:
                snippet = hit.snippet_text
                snippet = self.formatter.highlight_search_keyword(snippet, search_result.keyword)
                lines.append(f"   Page {hit.page_number}: {snippet}")

            if len(document_hits) > 3:
                lines.append(f"   ...and {len(document_hits) - 3} more pages with hits")

            lines.append("")

        total_document_count = len(hits_grouped_by_document)
        if total_document_count > displayed_document_count:
            remaining_documents = total_document_count - displayed_document_count
            lines.append(f"... and {remaining_documents} more documents")

        return "\n".join(lines)

    def _generate_no_results_message(self, search_result):
        """Generate appropriate message when no results are found."""
        if search_result.offset > 0:
            return f"No more results found for '{search_result.keyword}' at offset {search_result.offset}. Total results: {search_result.total_hits}"
        return f"No results found for '{search_result.keyword}'. make sure to use \"\" "

    def format_search_results_with_summary(
        self,
        search_result: SearchResult,
        max_display: int,
        keyword: str,
    ) -> List[Any]:
        """Format complete search results with summary, table, and examples.

        Args:
            search_result: SearchResult containing hits and metadata
            max_display: Maximum number of documents to display
            keyword: Search keyword for browse examples

        Returns:
            List of formatted output items (strings, tables, etc.)
        """
        output = []

        formatted_table = self.format_search_results(search_result, max_display)

        if not formatted_table:
            return output

        # Get search summary and format it
        summary = search_result.extract_summary()
        summary_lines = self.formatter.format_search_summary(summary)
        output.extend(summary_lines)

        # Add the table
        output.append(formatted_table)

        # For Rich tables (not strings), add browse examples and remaining documents
        if not isinstance(formatted_table, str):
            grouped_hits = summary.grouped_hits
            example_lines = self.formatter.format_browse_example(grouped_hits, keyword)
            output.extend(example_lines)

            total_groups = len(grouped_hits)
            remaining_message = self.formatter.format_remaining_documents(total_groups, max_display)
            if remaining_message:
                output.append(remaining_message)

        return output

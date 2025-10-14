"""
Search display service for formatting search results.
"""

from ..formatters import PlainTextFormatter
from ..models import SearchResult


class SearchDisplayService:
    """Display service specifically for search operations."""

    def __init__(self, formatter=None):
        """
        Initialize the search display service.

        Args:
            formatter: Formatter instance to use (PlainTextFormatter or RichConsoleFormatter)
                      If None, defaults to PlainTextFormatter
        """
        self.formatter = formatter or PlainTextFormatter()

    def format_search_results(
        self,
        search_result: SearchResult,
        maximum_documents_to_display: int = 20,
    ):
        """
        Format search results by delegating to the formatter.

        Args:
            search_result: SearchResult containing hits and metadata
            maximum_documents_to_display: Maximum number of documents to display

        Returns:
            Formatted search results (type depends on formatter: Table for Rich, str for Plain)
        """
        return self.formatter.format_search_results(search_result, maximum_documents_to_display)

    def format_search_results_with_summary(
        self,
        search_result: SearchResult,
        max_display: int,
        keyword: str,
    ) -> list:
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

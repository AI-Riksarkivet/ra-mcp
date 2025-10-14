"""
Browse display service for formatting browse results.
"""

from typing import List, Optional, Union, Dict
from ..formatters import PlainTextFormatter
from ..models import BrowseResult


class BrowseDisplayService:
    """Display service specifically for browse operations."""

    def __init__(self, formatter=None):
        """
        Initialize the browse display service.

        Args:
            formatter: Formatter instance to use (PlainTextFormatter or RichConsoleFormatter)
                      If None, defaults to PlainTextFormatter
        """
        self.formatter = formatter or PlainTextFormatter()

    def format_browse_results(
        self,
        operation: BrowseResult,
        highlight_term: Optional[str] = None,
        show_links: bool = False,
        show_success_message: bool = True,
    ):
        """
        Format browse results by delegating to the formatter.

        Args:
            operation: BrowseResult containing page contexts and metadata
            highlight_term: Optional term to highlight in text
            show_links: Whether to show ALTO/Image/Bildvisning links section
            show_success_message: Whether to show success message (CLI only)

        Returns:
            Formatted browse results (type depends on formatter: list for Rich, str for Plain)
        """
        return self.formatter.format_browse_results(operation, highlight_term, show_links, show_success_message)

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

    def format_browse_error(self, reference_code: str) -> List[str]:
        """Format error message for failed browse operation.

        Args:
            reference_code: The reference code that failed to load

        Returns:
            List of formatted error message lines
        """
        return [
            f"[red]Could not load pages for {reference_code}[/red]",
            "[yellow]Suggestions:[/yellow]",
            "• Check the reference code format",
            "• Try different page numbers",
            "• The document might not have transcriptions",
        ]

    def format_browse_header(self, reference_code: str) -> str:
        """Format browse operation header.

        Args:
            reference_code: Document reference code being browsed

        Returns:
            Formatted header message
        """
        return f"[blue]Looking up reference code: {reference_code}[/blue]"

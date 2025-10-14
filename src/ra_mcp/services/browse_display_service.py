"""
Browse display service for formatting browse results.
"""

from typing import List, Optional, Union, Any, Dict
from .base_display_service import BaseDisplayService
from ..models import BrowseResult


class BrowseDisplayService(BaseDisplayService):
    """Display service specifically for browse operations."""

    def format_browse_results(
        self,
        operation: BrowseResult,
        highlight_term: Optional[str] = None,
        show_links: bool = False,
        show_success_message: bool = True,
    ) -> Union[List[Any], str]:
        """Format browse results as Rich Panel objects for CLI or string for MCP.

        Args:
            operation: BrowseResult containing page contexts and metadata
            highlight_term: Optional term to highlight in text
            show_links: Whether to show ALTO/Image/Bildvisning links section
            show_success_message: Whether to show success message (CLI only)
        """
        # For CLI mode with Rich formatter, use advanced formatting
        if self.show_border and hasattr(self.formatter, "format_browse_results_grouped"):
            return self.formatter.format_browse_results_grouped(
                operation,
                highlight_term,
                show_links,
                show_success_message
            )

        # For MCP mode or fallback, use string formatting without borders
        if not operation.contexts:
            return f"No page contexts found for {operation.reference_code}"

        lines = []
        lines.append(f"📚 Document: {operation.reference_code}")

        # Add rich metadata if available
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

        lines.append(f"📖 Pages loaded: {len(operation.contexts)}")
        lines.append("")

        for context in operation.contexts:
            lines.append(f"📄 Page {context.page_number}")

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

        return "\n".join(lines)

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
            "• The document might not have transcriptions"
        ]

    def format_browse_header(self, reference_code: str) -> str:
        """Format browse operation header.

        Args:
            reference_code: Document reference code being browsed

        Returns:
            Formatted header message
        """
        return f"[blue]Looking up reference code: {reference_code}[/blue]"

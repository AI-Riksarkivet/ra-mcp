"""
Unified display service that can format output for different interfaces (CLI with rich, MCP with plain text).
This eliminates formatting code duplication between CLI and MCP tools.
"""

import re
from typing import List, Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod

from ..models import SearchHit, PageContext
from .search_operations import SearchOperation, BrowseOperation, SearchResultsAnalyzer


class OutputFormatter(Protocol):
    """Protocol for different output formatters (rich console, plain text, etc.)."""

    def format_text(self, text: str, style: str = "") -> str:
        """Format text with optional styling."""
        ...

    def format_table(self, headers: List[str], rows: List[List[str]], title: str = "") -> str:
        """Format a table."""
        ...

    def format_panel(self, content: str, title: str = "", border_style: str = "") -> str:
        """Format a panel/box with content."""
        ...

    def keyword_highlight(self, text: str, keyword: str) -> str:
        """Highlight keyword in text."""
        ...


class RichConsoleFormatter:
    """Rich console formatter for CLI output."""

    def format_text(self, text: str, style: str = "") -> str:
        """Format text with rich markup."""
        if style:
            return f"[{style}]{text}[/{style}]"
        return text

    def format_table(self, headers: List[str], rows: List[List[str]], title: str = "") -> str:
        """Format a rich table - this will be handled by calling code with Rich directly."""
        # This is a placeholder - actual Rich table creation happens in the calling code
        return f"TABLE: {title}\nHeaders: {headers}\nRows: {len(rows)}"

    def format_panel(self, content: str, title: str = "", border_style: str = "") -> str:
        """Format a rich panel - this will be handled by calling code with Rich directly."""
        # This is a placeholder - actual Rich panel creation happens in the calling code
        return f"PANEL: {title}\n{content}"

    def keyword_highlight(self, text: str, keyword: str) -> str:
        """Highlight keyword with rich markup."""
        if not keyword:
            return text
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(lambda m: f"[bold yellow underline]{m.group()}[/bold yellow underline]", text)


class PlainTextFormatter:
    """Plain text formatter for MCP output."""

    def format_text(self, text: str, style: str = "") -> str:
        """Format text as plain text (ignore styling)."""
        return text

    def format_table(self, headers: List[str], rows: List[List[str]], title: str = "") -> str:
        """Format a simple text table."""
        lines = []
        if title:
            lines.append(f"# {title}")
            lines.append("")

        # Calculate column widths
        all_rows = [headers] + rows
        col_widths = [max(len(str(row[i])) for row in all_rows) for i in range(len(headers))]

        # Format header
        header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Format rows
        for row in rows:
            row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
            lines.append(row_line)

        return "\n".join(lines)

    def format_panel(self, content: str, title: str = "", border_style: str = "") -> str:
        """Format a simple text panel."""
        lines = []
        if title:
            lines.append(f"## {title}")
            lines.append("")
        lines.append(content)
        return "\n".join(lines)

    def keyword_highlight(self, text: str, keyword: str) -> str:
        """Highlight keyword with simple markers."""
        if not keyword:
            return text
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(lambda m: f"**{m.group()}**", text)


class UnifiedDisplayService:
    """
    Unified display service that can format output for different interfaces.
    Uses different formatters for CLI (rich) vs MCP (plain text).
    """

    def __init__(self, formatter: OutputFormatter):
        self.formatter = formatter
        self.analyzer = SearchResultsAnalyzer()

    def format_search_results(
        self,
        operation: SearchOperation,
        max_display: int = 20,
        show_context: bool = False
    ) -> str:
        """Format search results with the configured formatter."""
        if not operation.hits:
            return "No search hits found."

        summary = self.analyzer.extract_search_summary(operation)
        grouped_hits = summary['grouped_hits']

        lines = []
        lines.append(f"Found {summary['page_hits_returned']} page-level hits across {summary['documents_returned']} documents")

        if not show_context:
            lines.append("💡 Tips: Use --context to see full page transcriptions | Use 'browse' command to view specific reference codes")

        lines.append("")

        # Format results by document
        displayed_groups = 0
        for ref_code, ref_hits in grouped_hits.items():
            if displayed_groups >= max_display:
                break
            displayed_groups += 1

            # Document header
            first_hit = ref_hits[0]
            lines.append(f"📚 Document: {ref_code}")

            # Institution info
            if first_hit.archival_institution:
                institution = first_hit.archival_institution[0].get('caption', '')
                if institution:
                    lines.append(f"🏛️  Institution: {institution}")

            # Date
            if first_hit.date:
                lines.append(f"📅 Date: {first_hit.date}")

            # Title
            title = first_hit.title[:100] + '...' if len(first_hit.title) > 100 else first_hit.title
            lines.append(f"📄 Title: {title}")

            # Pages
            pages = sorted(set(h.page_number for h in ref_hits))
            pages_trimmed = [p.lstrip('0') or '0' for p in pages]
            lines.append(f"📖 Pages with hits: {', '.join(pages_trimmed)}")

            # Content snippets or full text
            if show_context and operation.enriched:
                # Show full page content
                for hit in ref_hits[:3]:
                    if hit.full_page_text:
                        is_search_hit = hit.snippet_text != "[Context page - no search hit]"
                        page_type = "SEARCH HIT" if is_search_hit else "context"

                        lines.append(f"\n   📄 Page {hit.page_number} ({page_type}):")

                        display_text = hit.full_page_text
                        if is_search_hit:
                            display_text = self.formatter.keyword_highlight(display_text, operation.keyword)

                        # Truncate for display
                        if len(display_text) > 500:
                            display_text = display_text[:500] + "..."

                        lines.append(f"   {display_text}")
            else:
                # Show snippets
                for hit in ref_hits[:3]:
                    snippet = hit.snippet_text[:150] + '...' if len(hit.snippet_text) > 150 else hit.snippet_text
                    snippet = self.formatter.keyword_highlight(snippet, operation.keyword)
                    lines.append(f"   Page {hit.page_number}: {snippet}")

            if len(ref_hits) > 3:
                lines.append(f"   ...and {len(ref_hits) - 3} more pages with hits")

            lines.append("")

        # Show remaining results info
        total_groups = len(grouped_hits)
        if total_groups > displayed_groups:
            remaining = total_groups - displayed_groups
            lines.append(f"... and {remaining} more documents")

        return "\n".join(lines)

    def format_browse_results(
        self,
        operation: BrowseOperation,
        highlight_term: Optional[str] = None
    ) -> str:
        """Format browse results with the configured formatter."""
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
                display_text = self.formatter.keyword_highlight(display_text, highlight_term)

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
        no_grouping: bool = False
    ) -> str:
        """Format show-pages results (search + context)."""
        if not enriched_hits:
            return f"No pages found containing '{search_op.keyword}'"

        lines = []
        lines.append(f"🔍 Search results for '{search_op.keyword}':")
        lines.append(f"Found {len(search_op.hits)} initial hits, showing {len(enriched_hits)} pages with context")
        lines.append("")

        if no_grouping:
            # Show individual pages
            for hit in enriched_hits:
                if hit.full_page_text:
                    is_search_hit = hit.snippet_text != "[Context page - no search hit]"
                    page_type = "🎯 SEARCH HIT" if is_search_hit else "📄 context"

                    lines.append(f"{page_type}: {hit.reference_code} - Page {hit.page_number}")
                    lines.append("─" * 60)

                    display_text = hit.full_page_text
                    if is_search_hit:
                        display_text = self.formatter.keyword_highlight(display_text, search_op.keyword)

                    lines.append(display_text)
                    lines.append("")
        else:
            # Group by document
            grouped = self.analyzer.group_hits_by_document(enriched_hits)

            for doc_ref, doc_hits in grouped.items():
                # Sort by page number
                doc_hits.sort(key=lambda h: int(h.page_number) if h.page_number.isdigit() else 0)

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
                            display_text = self.formatter.keyword_highlight(display_text, search_op.keyword)
                        lines.append(display_text)
                    else:
                        lines.append("No text content available")

                    lines.append("")

                lines.append("")

        return "\n".join(lines)

    def format_document_structure(self, collection_info: Dict[str, Any]) -> str:
        """Format document structure information."""
        if not collection_info:
            return "No document structure information available"

        lines = []
        lines.append(f"📚 Collection: {collection_info.get('title', 'Unknown')}")
        lines.append(f"🔗 Collection URL: {collection_info.get('collection_url', '')}")
        lines.append("")

        manifests = collection_info.get('manifests', [])
        if manifests:
            lines.append(f"📖 Available manifests ({len(manifests)}):")
            for manifest in manifests:
                lines.append(f"  • {manifest.get('label', 'Untitled')} ({manifest.get('id', '')})")
                lines.append(f"    URL: {manifest.get('url', '')}")
        else:
            lines.append("No manifests found")

        return "\n".join(lines)

    def format_error(self, error_msg: str, suggestions: List[str] = None) -> str:
        """Format error message with suggestions."""
        lines = [f"❌ Error: {error_msg}"]

        if suggestions:
            lines.append("")
            lines.append("💡 Suggestions:")
            for suggestion in suggestions:
                lines.append(f"  • {suggestion}")

        return "\n".join(lines)
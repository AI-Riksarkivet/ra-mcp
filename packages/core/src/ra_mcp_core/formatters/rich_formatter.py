"""
Rich console formatter for CLI output.
Creates actual Rich objects (Tables, Panels) for console display.
"""

import re
from typing import List, Dict, Union, Optional, Any
from rich.table import Table
from rich.panel import Panel
from rich.console import Console, Group

from .base_formatter import BaseFormatter
from ..models import SearchResult, PageContext, SearchHit, SearchSummary, BrowseResult
from .utils import (
    trim_page_number,
    trim_page_numbers,
    truncate_text,
    extract_institution,
    format_example_browse_command,
)


class RichConsoleFormatter(BaseFormatter):
    """
    Formatter that creates Rich objects for console output.
    This formatter is used by DisplayService for CLI display.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the Rich formatter.

        Args:
            console: Optional Console instance for rendering
        """
        self.console = console or Console()

    def format_text(self, text_content: str, style_name: str = "") -> str:
        """Format text with Rich markup."""
        if style_name:
            return f"[{style_name}]{text_content}[/{style_name}]"
        return text_content

    def format_table(
        self,
        column_headers: List[str],
        table_rows: List[List[str]],
        table_title: str = "",
    ) -> Table:
        """
        Create a Rich Table object.

        Args:
            column_headers: List of column headers
            table_rows: List of row data
            table_title: Optional table title

        Returns:
            Rich Table object
        """
        table = Table(
            *column_headers,
            title=table_title if table_title else None,
            show_lines=True,
            expand=True,
        )

        for row in table_rows:
            table.add_row(*row)

        return table

    def format_panel(
        self,
        panel_content: str,
        panel_title: str = "",
        panel_border_style: str = "green",
    ) -> Panel:
        """
        Create a Rich Panel object.

        Args:
            panel_content: Content to display in the panel
            panel_title: Optional panel title
            panel_border_style: Border style (default: green)

        Returns:
            Rich Panel object
        """
        return Panel(
            panel_content,
            title=panel_title if panel_title else None,
            border_style=panel_border_style,
            padding=(0, 1),
        )

    def highlight_search_keyword(self, text_content: str, search_keyword: str) -> str:
        """
        Highlight search keywords using Rich markup.
        First converts **text** markers from API to Rich highlighting.
        Then highlights the search keyword if no markers present.

        Args:
            text_content: Text to search in
            search_keyword: Keyword to highlight

        Returns:
            Text with highlighted keywords
        """
        if re.search(r"\*\*[^*]+\*\*", text_content):
            return re.sub(
                r"\*\*(.*?)\*\*",
                r"[bold yellow underline]\1[/bold yellow underline]",
                text_content,
            )

        if not search_keyword:
            return text_content
        keyword_pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
        return keyword_pattern.sub(
            lambda match: f"[bold yellow underline]{match.group()}[/bold yellow underline]",
            text_content,
        )

    def format_search_results(self, search_result: SearchResult, max_display: int = 20) -> Union[Table, str]:
        """
        Format search results as a Rich Table for CLI display.

        Args:
            search_result: Search operation with hits and metadata
            max_display: Maximum number of documents to display

        Returns:
            Rich Table object (if results found) or formatted string (if no results)
        """
        if not search_result.hits:
            return self.format_no_results_message(search_result)

        summary = search_result.extract_summary()
        grouped_hits = summary.grouped_hits

        table = Table(
            "Institution & Reference",
            "Content",
            title=f"Search Results for '{search_result.keyword}'",
            show_lines=True,
            expand=True,
        )

        displayed_groups = 0
        for ref_code, ref_hits in grouped_hits.items():
            if displayed_groups >= max_display:
                break
            displayed_groups += 1

            first_hit = ref_hits[0]

            # Build institution and reference column
            institution = extract_institution(first_hit)
            institution_and_ref = ""
            if institution:
                institution_and_ref = f"🏛️  {truncate_text(institution, 30)}\n"

            # Format page numbers with hit count
            pages = sorted(set(h.page_number for h in ref_hits))
            pages_trimmed = trim_page_numbers(pages)
            pages_str = ",".join(pages_trimmed)
            hit_count = len(ref_hits)
            hit_label = "hit" if hit_count == 1 else "hits"

            # Show total hits if available and different from shown count
            total_in_doc = first_hit.total_hits_in_document
            if total_in_doc and total_in_doc > hit_count:
                institution_and_ref += f'📚 "{ref_code}" --page "{pages_str}"\n💡 [dim]{hit_count} {hit_label} shown ({total_in_doc} total)[/dim]'
            else:
                institution_and_ref += f'📚 "{ref_code}" --page "{pages_str}"\n💡 [dim]{hit_count} {hit_label} found[/dim]'

            if first_hit.date:
                institution_and_ref += f"\n📅 [dim]{first_hit.date}[/dim]"

            # Build content column
            title_text = truncate_text(first_hit.title, 50)
            content_parts = []

            if title_text and title_text.strip():
                content_parts.append(f"[bold blue]{title_text}[/bold blue]")
            else:
                content_parts.append("[bright_black]No title[/bright_black]")

            # Add snippets
            for hit in ref_hits[:3]:
                snippet = truncate_text(hit.snippet_text, 150)
                snippet = self.highlight_search_keyword(snippet, search_result.keyword)
                trimmed_page = trim_page_number(hit.page_number)
                content_parts.append(f"[dim]Page {trimmed_page}:[/dim] [italic]{snippet}[/italic]")

            if len(ref_hits) > 3:
                content_parts.append(f"[dim]...and {len(ref_hits) - 3} more pages with hits[/dim]")

            table.add_row(institution_and_ref, "\n".join(content_parts))

        return table

    def format_page_context_panel(self, context: PageContext, highlight_term: str = "") -> Panel:
        """
        Create a Rich Panel for a single page context.

        Args:
            context: Page context with full text and metadata
            highlight_term: Optional term to highlight

        Returns:
            Rich Panel object
        """
        page_content = []

        # Full transcribed text with highlighting
        display_text = self.highlight_search_keyword(context.full_text, highlight_term)
        page_content.append(f"[italic]{display_text}[/italic]")

        # Links section
        page_content.append("\n[bold cyan]🔗 Links:[/bold cyan]")
        page_content.append(f"     [dim]📝 ALTO XML:[/dim] [link]{context.alto_url}[/link]")
        if context.image_url:
            page_content.append(f"     [dim]🖼️  Image:[/dim] [link]{context.image_url}[/link]")
        if context.bildvisning_url:
            page_content.append(f"     [dim]👁️  Bildvisning:[/dim] [link]{context.bildvisning_url}[/link]")

        trimmed_page = trim_page_number(str(context.page_number))
        panel_title = f"[cyan]Page {trimmed_page}: {context.reference_code or 'Unknown Reference'}[/cyan]"

        return self.format_panel("\n".join(page_content), panel_title=panel_title, panel_border_style="green")

    def format_search_summary(self, summary: SearchSummary) -> List[str]:
        """
        Format search summary information.

        Args:
            summary: Search summary with hit counts and metadata

        Returns:
            List of formatted summary lines
        """
        lines = []
        lines.append(
            f"\n[bold green]✓[/bold green] Found [bold]{summary.page_hits_returned}[/bold] page hits across [bold]{summary.documents_returned}[/bold] volumes"
        )

        if summary.total_hits > summary.page_hits_returned:
            lines.append(f"[dim]   (Total {summary.total_hits} hits available, showing from offset {summary.offset})[/dim]")

        return lines

    def format_browse_example(self, grouped_hits: Dict[str, List[SearchHit]], keyword: str) -> List[str]:
        """
        Format an example browse command.

        Args:
            grouped_hits: Dictionary of grouped hits by reference
            keyword: Search keyword

        Returns:
            List of formatted command lines
        """
        if not grouped_hits:
            return []

        lines = []
        first_ref = next(iter(grouped_hits.keys()))
        first_group = grouped_hits[first_ref]
        pages = sorted(set(h.page_number for h in first_group))
        pages_trimmed = trim_page_numbers(pages[:5])

        lines.append("\n[dim]💡 Example: To view these hits, run:[/dim]")
        cmd = format_example_browse_command(first_ref, pages_trimmed, keyword)
        lines.append(f"[cyan]   {cmd}[/cyan]")

        return lines

    def format_remaining_documents(self, total: int, displayed: int) -> str:
        """
        Format remaining documents message.

        Args:
            total: Total number of documents
            displayed: Number of documents displayed

        Returns:
            Formatted message or empty string
        """
        if total > displayed:
            remaining = total - displayed
            return f"\n[dim]... and {remaining} more documents[/dim]"
        return ""

    def format_no_results_message(self, search_result) -> str:
        """
        Generate appropriate message when no results are found.

        Args:
            search_result: SearchResult containing keyword, offset, and total_hits

        Returns:
            Formatted Rich markup message
        """
        if search_result.offset > 0:
            return f"[yellow]No more results found for '{search_result.keyword}' at offset {search_result.offset}. Total results: {search_result.total_hits}[/yellow]"
        return f"[yellow]No results found for '{search_result.keyword}'. Make sure to use \"\" for exact phrases.[/yellow]"

    def format_browse_results(
        self,
        browse_result: BrowseResult,
        highlight_term: Optional[str] = None,
        show_links: bool = False,
        show_success_message: bool = True,
    ) -> List[Any]:
        """
        Format browse results as grouped Rich panels with metadata for CLI display.

        Args:
            browse_result: BrowseResult containing contexts and metadata
            highlight_term: Optional term to highlight in text
            show_links: Whether to show ALTO/Image/Bildvisning links section
            show_success_message: Whether to print success message

        Returns:
            List containing optional success message and panel objects
        """
        output = []

        if show_success_message:
            output.append(f"[green]Successfully loaded {len(browse_result.contexts)} pages[/green]")

        # Group page contexts by reference code
        grouped_contexts = {}
        for context in browse_result.contexts:
            ref_code = context.reference_code
            if ref_code not in grouped_contexts:
                grouped_contexts[ref_code] = []
            grouped_contexts[ref_code].append(context)

        # Display results grouped by document
        for ref_code, contexts in grouped_contexts.items():
            # Sort pages by page number
            sorted_contexts = sorted(contexts, key=lambda c: c.page_number)

            renderables = []

            # Add document metadata at the top of the panel if available
            if browse_result.document_metadata:
                metadata = browse_result.document_metadata

                # Create left column content (basic info)
                left_content = []
                left_content.append(f"[bold blue]📄 Volume:[/bold blue] {ref_code}")

                # Display title
                if metadata.title and metadata.title != "(No title)":
                    left_content.append(f"[blue]📋 Title:[/blue] {metadata.title}")

                # Display date range
                if metadata.date:
                    left_content.append(f"[blue]📅 Date:[/blue] {metadata.date}")

                # Display archival institution
                if metadata.archival_institution:
                    institutions = metadata.archival_institution
                    if institutions:
                        inst_names = [inst.get("caption", "") for inst in institutions]
                        left_content.append(f"[blue]🏛️  Institution:[/blue] {', '.join(inst_names)}")

                # Create right column content (hierarchy)
                right_content = []
                if metadata.hierarchy:
                    hierarchy = metadata.hierarchy
                    if hierarchy:
                        for i, level in enumerate(hierarchy):
                            caption = level.get("caption", "")
                            caption = caption.replace("\n", " ").strip()

                            if i == 0:
                                right_content.append(f"📁 {caption}")
                            elif i == len(hierarchy) - 1:
                                indent = "  " * i
                                right_content.append(f"{indent}└── 📄 {caption}")
                            else:
                                indent = "  " * i
                                right_content.append(f"{indent}├── 📁 {caption}")

                # Create clean two-column layout using Rich Table
                if right_content:
                    metadata_table = Table.grid(padding=(0, 2))
                    metadata_table.add_column(justify="left", ratio=1)
                    metadata_table.add_column(justify="left", ratio=1)

                    left_text = "\n".join(left_content)
                    right_text = "\n".join(right_content)

                    metadata_table.add_row(left_text, right_text)
                    renderables.append(metadata_table)
                else:
                    renderables.append("\n".join(left_content))

                # Display note on its own row if available
                if metadata.note:
                    renderables.append(f"[blue]📝 Note:[/blue] {metadata.note}")

                renderables.append("")
            else:
                # If no metadata available, just show the document header
                renderables.append(f"[bold blue]📄 Volume:[/bold blue] {ref_code}")
                renderables.append("")

            panel_content = []

            for context in sorted_contexts:
                # Add page separator with optional bildvisning link
                if show_links:
                    # When showing all links below, keep simple separator
                    panel_content.append(f"[dim]────── Page {context.page_number} ──────[/dim]")
                else:
                    # When not showing links section, include bildvisning link in separator
                    if context.bildvisning_url:
                        panel_content.append(f"[dim]────── Page {context.page_number} | [/dim][link]{context.bildvisning_url}[/link][dim] ──────[/dim]")
                    else:
                        panel_content.append(f"[dim]────── Page {context.page_number} ──────[/dim]")

                # Add page content with highlighting
                display_text = context.full_text
                if highlight_term:
                    display_text = self.highlight_search_keyword(display_text, highlight_term)
                panel_content.append(f"[italic]{display_text}[/italic]")

                # Add links if requested
                if show_links:
                    panel_content.append("\n[bold cyan]🔗 Links:[/bold cyan]")
                    panel_content.append(f"     [dim]📝 ALTO XML:[/dim] [link]{context.alto_url}[/link]")
                    if context.image_url:
                        panel_content.append(f"     [dim]🖼️  Image:[/dim] [link]{context.image_url}[/link]")
                    if context.bildvisning_url:
                        panel_content.append(f"     [dim]👁️  Bildvisning:[/dim] [link]{context.bildvisning_url}[/link]")

                # Add spacing between pages (except for the last one)
                if context != sorted_contexts[-1]:
                    panel_content.append("")

            # Add page content to renderables
            for line in panel_content:
                renderables.append(line)

            # Create the grouped panel using Rich Group
            panel_group = Group(*renderables)
            grouped_panel = Panel(
                panel_group,
                title=None,
                border_style="green",
                padding=(1, 1),
            )
            output.append("")  # Add spacing before the panel
            output.append(grouped_panel)

        return output

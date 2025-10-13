"""
Rich console formatter for CLI output.
Creates actual Rich objects (Tables, Panels) for console display.
"""

import re
from typing import List, Dict, Union, Optional
from rich.table import Table
from rich.panel import Panel
from rich.console import Console

from .base_formatter import BaseFormatter
from ..models import SearchResult, PageContext, SearchHit, SearchSummary
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

    def format_search_results_table(self, search_result: SearchResult, max_display: int = 20) -> Union[Table, str]:
        """
        Create a Rich Table for search results.

        Args:
            search_result: Search operation with hits and metadata
            max_display: Maximum number of documents to display

        Returns:
            Rich Table object or message string if no hits
        """
        if not search_result.hits:
            return "[yellow]No search hits found.[/yellow]"

        from ..services import analysis

        summary = analysis.extract_search_summary(search_result)
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

            # Format page numbers
            pages = sorted(set(h.page_number for h in ref_hits))
            pages_trimmed = trim_page_numbers(pages)
            pages_str = ",".join(pages_trimmed)
            institution_and_ref += f'📚 "{ref_code}" --page "{pages_str}"'

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
        lines.append(f"\n[bold green]✓[/bold green] Found [bold]{summary.page_hits_returned}[/bold] page hits across [bold]{summary.documents_returned}[/bold] volumes")

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

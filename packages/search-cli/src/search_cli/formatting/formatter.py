"""
Rich console formatter for CLI output.
Creates actual Rich objects (Tables, Panels) for console display.
"""

import re
from typing import List, Dict, Union, Optional, Any
from rich.table import Table
from rich.panel import Panel
from rich.console import Console, Group

from ra_mcp_search.models import SearchResult, SearchRecord
from .utils import (
    trim_page_number,
    trim_page_numbers,
    truncate_text,
    format_example_browse_command,
)


class RichConsoleFormatter:
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
            search_result: Search operation with documents and metadata
            max_display: Maximum number of documents to display

        Returns:
            Rich Table object (if results found) or formatted string (if no results)
        """
        if not search_result.items:
            return self.format_no_results_message(search_result)

        table = Table(
            "Institution & Reference",
            "Content",
            title=f"Search Results for '{search_result.keyword}'",
            show_lines=True,
            expand=True,
        )

        for idx, document in enumerate(search_result.items[:max_display]):
            # Build institution and reference column
            institution_and_ref = ""
            if document.metadata.archival_institution:
                institution = document.metadata.archival_institution[0].caption
                institution_and_ref = f"🏛️  {truncate_text(institution, 30)}\n"

            # Handle records with transcribed text snippets
            if document.transcribed_text and document.transcribed_text.snippets:
                # Extract unique page numbers from all snippets
                pages = sorted(set(
                    page.id
                    for snippet in document.transcribed_text.snippets
                    for page in snippet.pages
                ))
                pages_trimmed = trim_page_numbers(pages)
                pages_str = ",".join(pages_trimmed)

                # Show snippet count vs total hits
                snippet_count = len(document.transcribed_text.snippets)
                total_hits = document.get_total_hits()
                hit_label = "hit" if snippet_count == 1 else "hits"

                if total_hits > snippet_count:
                    institution_and_ref += f'📚 "{document.metadata.reference_code}" --page "{pages_str}"\n💡 [dim]{snippet_count} {hit_label} shown ({total_hits} total)[/dim]'
                else:
                    institution_and_ref += f'📚 "{document.metadata.reference_code}" --page "{pages_str}"\n💡 [dim]{snippet_count} {hit_label} found[/dim]'
            else:
                # For metadata-only results (no transcription snippets)
                institution_and_ref += f'📚 "{document.metadata.reference_code}"\n💡 [dim]Metadata match[/dim]'

            if document.metadata.date:
                institution_and_ref += f"\n📅 [dim]{document.metadata.date}[/dim]"

            # Build content column
            title_text = truncate_text(document.get_title(), 50)
            content_parts = []

            if title_text and title_text.strip() and title_text != "(No title)":
                content_parts.append(f"[bold blue]{title_text}[/bold blue]")
            else:
                content_parts.append("[bright_black](No title)[/bright_black]")

            # Add object type and type
            type_info = f"{document.object_type}"
            if document.type:
                type_info += f" / {document.type}"
            content_parts.append(f"[yellow]🏷️  {type_info}[/yellow]")

            # Add hierarchy information for metadata searches
            if document.metadata.hierarchy:
                hierarchy_parts = [h.caption for h in document.metadata.hierarchy]
                if hierarchy_parts:
                    hierarchy_text = " → ".join(hierarchy_parts[:3])  # Show up to 3 levels
                    content_parts.append(f"[cyan]📂 {truncate_text(hierarchy_text, 150)}[/cyan]")

            # Add provenance (creator) information
            if document.metadata.provenance:
                prov = document.metadata.provenance[0]
                prov_text = prov.caption
                if prov.date:
                    prov_text += f" ({prov.date})"
                content_parts.append(f"[green]👤 {truncate_text(prov_text, 100)}[/green]")

            # Add note if available (useful for metadata searches)
            if document.metadata.note:
                note_text = truncate_text(document.metadata.note, 250)
                content_parts.append(f"[dim]📝 {note_text}[/dim]")

            # Add snippets if available (for transcribed text searches)
            if document.transcribed_text and document.transcribed_text.snippets:
                for snippet in document.transcribed_text.snippets[:3]:
                    snippet_text = truncate_text(snippet.text, 150)
                    snippet_text = self.highlight_search_keyword(snippet_text, search_result.keyword)

                    # Get first page number for this snippet
                    if snippet.pages:
                        trimmed_page = trim_page_number(snippet.pages[0].id)
                        content_parts.append(f"[dim]Page {trimmed_page}:[/dim] [italic]{snippet_text}[/italic]")

                if len(document.transcribed_text.snippets) > 3:
                    content_parts.append(f"[dim]...and {len(document.transcribed_text.snippets) - 3} more pages with hits[/dim]")

            table.add_row(institution_and_ref, "\n".join(content_parts))

        return table

    def format_search_summary_stats(
        self,
        snippet_count: int,
        records_count: int,
        total_hits: int,
        offset: int
    ) -> List[str]:
        """
        Format search summary statistics.

        Args:
            snippet_count: Number of snippets/page hits returned
            records_count: Number of records/documents returned
            total_hits: Total number of records matching query
            offset: Pagination offset

        Returns:
            List of formatted summary lines
        """
        lines = []
        lines.append(
            f"\n[bold green]✓[/bold green] Found [bold]{snippet_count}[/bold] page hits across [bold]{records_count}[/bold] volumes"
        )

        if total_hits > records_count:
            lines.append(f"[dim]   (Total {total_hits} hits available, showing from offset {offset})[/dim]")

        return lines

    def format_browse_example(self, documents: List[SearchRecord], keyword: str) -> List[str]:
        """
        Format an example browse command.

        Args:
            documents: List of SearchRecord objects
            keyword: Search keyword

        Returns:
            List of formatted command lines
        """
        if not documents:
            return []

        # Get first document with snippets
        first_doc = None
        for doc in documents:
            if doc.transcribed_text and doc.transcribed_text.snippets:
                first_doc = doc
                break

        if not first_doc:
            return []

        lines = []
        ref_code = first_doc.metadata.reference_code

        # Extract page numbers from snippets
        pages = sorted(set(
            page.id
            for snippet in first_doc.transcribed_text.snippets
            for page in snippet.pages
        ))
        pages_trimmed = trim_page_numbers(pages[:5])

        lines.append("\n[dim]💡 Example: To view these hits, run:[/dim]")
        cmd = format_example_browse_command(ref_code, pages_trimmed, keyword)
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

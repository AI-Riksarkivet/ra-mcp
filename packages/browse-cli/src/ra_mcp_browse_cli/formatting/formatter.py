"""
Rich console formatter for CLI output.
Creates actual Rich objects (Tables, Panels) for console display.
"""

import re
from typing import Any

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table

from ra_mcp_browse.models import BrowseResult, PageContext
from ra_mcp_search.models import SearchRecord, SearchResult

from .utils import (
    format_example_browse_command,
    trim_page_number,
    trim_page_numbers,
    truncate_text,
)


class RichConsoleFormatter:
    """
    Formatter that creates Rich objects for console output.
    This formatter is used by DisplayService for CLI display.
    """

    def __init__(self, console: Console | None = None):
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
        column_headers: list[str],
        table_rows: list[list[str]],
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

    def format_search_results(self, search_result: SearchResult, max_display: int = 20) -> Table | str:
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

        for _idx, document in enumerate(search_result.items[:max_display]):
            if not document.transcribed_text or not document.transcribed_text.snippets:
                continue

            # Build institution and reference column
            institution_and_ref = ""
            if document.metadata.archival_institution:
                institution = document.metadata.archival_institution[0].caption
                institution_and_ref = f"🏛️  {truncate_text(institution, 30)}\n"

            # Extract unique page numbers from all snippets
            pages = sorted({page.id for snippet in document.transcribed_text.snippets for page in snippet.pages})
            pages_trimmed = trim_page_numbers(pages)
            pages_str = ",".join(pages_trimmed)

            # Show snippet count vs total hits
            snippet_count = len(document.transcribed_text.snippets)
            total_hits = document.get_total_hits()
            hit_label = "hit" if snippet_count == 1 else "hits"

            if total_hits > snippet_count:
                institution_and_ref += (
                    f'📚 "{document.metadata.reference_code}" --page "{pages_str}"\n💡 [dim]{snippet_count} {hit_label} shown ({total_hits} total)[/dim]'
                )
            else:
                institution_and_ref += f'📚 "{document.metadata.reference_code}" --page "{pages_str}"\n💡 [dim]{snippet_count} {hit_label} found[/dim]'

            if document.metadata.date:
                institution_and_ref += f"\n📅 [dim]{document.metadata.date}[/dim]"

            # Build content column
            title_text = truncate_text(document.get_title(), 50)
            content_parts = []

            if title_text and title_text.strip() and title_text != "(No title)":
                content_parts.append(f"[bold blue]{title_text}[/bold blue]")
            else:
                content_parts.append("[bright_black](No title)[/bright_black]")

            # Add snippets (up to 3)
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

    def format_search_summary_stats(self, snippet_count: int, records_count: int, total_hits: int, offset: int) -> list[str]:
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
        lines.append(f"\n[bold green]✓[/bold green] Found [bold]{snippet_count}[/bold] page hits across [bold]{records_count}[/bold] volumes")

        if total_hits > records_count:
            lines.append(f"[dim]   (Total {total_hits} hits available, showing from offset {offset})[/dim]")

        return lines

    def format_browse_example(self, documents: list[SearchRecord], keyword: str) -> list[str]:
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
        if first_doc.transcribed_text and first_doc.transcribed_text.snippets:
            pages = sorted({page.id for snippet in first_doc.transcribed_text.snippets for page in snippet.pages})
        else:
            pages = []
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

    def _format_non_digitised_panel(self, browse_result: BrowseResult) -> list[Any]:
        """Format metadata panel for non-digitised materials."""
        output: list[Any] = []
        output.append("[yellow]⚠️  This material is not digitised or transcribed - no page images or text available.[/yellow]")
        output.append("[dim]Showing metadata only:[/dim]\n")

        metadata = browse_result.oai_metadata
        if metadata is None:
            return output
        metadata_parts = []
        metadata_parts.append(f"[bold blue]📄 Reference Code:[/bold blue] {browse_result.reference_code}")

        if metadata.title and metadata.title != "(No title)":
            metadata_parts.append(f"[blue]📋 Title:[/blue] {metadata.title}")

        if metadata.unitdate:
            metadata_parts.append(f"[blue]📅 Date Range:[/blue] {metadata.unitdate}")

        if metadata.repository:
            metadata_parts.append(f"[blue]🏛️  Repository:[/blue] {metadata.repository}")

        if metadata.unitid and metadata.unitid != browse_result.reference_code:
            metadata_parts.append(f"[blue]🔖 Unit ID:[/blue] {metadata.unitid}")

        if metadata.description:
            desc = metadata.description
            if len(desc) > 300:
                desc = desc[:297] + "..."
            metadata_parts.append(f"[blue]📝 Description:[/blue] {desc}")

        if metadata.nad_link:
            metadata_parts.append(f"[blue]🔗 View Online:[/blue] {metadata.nad_link}")

        if metadata.iiif_manifest:
            metadata_parts.append(f"[magenta]🖼️  IIIF Manifest:[/magenta] {metadata.iiif_manifest}")

        if metadata.iiif_image:
            metadata_parts.append(f"[cyan]🎨 Preview Image:[/cyan] {metadata.iiif_image}")

        if metadata.datestamp:
            metadata_parts.append(f"[dim]🕒 Last Updated:[/dim] {metadata.datestamp}")

        panel = Panel(
            "\n".join(metadata_parts),
            title="[yellow]Non-Digitised Material[/yellow]",
            border_style="yellow",
        )
        output.append(panel)
        return output

    def _format_group_metadata(self, renderables: list[Any], metadata, ref_code: str) -> None:
        """Format OAI-PMH metadata section at the top of a grouped panel."""
        left_content = []
        left_content.append(f"[bold blue]📄 Volume:[/bold blue] {ref_code}")

        if metadata.title and metadata.title != "(No title)":
            left_content.append(f"[blue]📋 Title:[/blue] {metadata.title}")

        if metadata.unitdate:
            left_content.append(f"[blue]📅 Date Range:[/blue] {metadata.unitdate}")

        if metadata.repository:
            left_content.append(f"[blue]🏛️  Repository:[/blue] {metadata.repository}")

        if metadata.unitid and metadata.unitid != ref_code:
            left_content.append(f"[blue]🔖 Unit ID:[/blue] {metadata.unitid}")

        if metadata.description:
            desc = metadata.description
            if len(desc) > 200:
                desc = desc[:197] + "..."
            left_content.append(f"[dim]📝 {desc}[/dim]")

        renderables.append("\n".join(left_content))

        if metadata.nad_link:
            renderables.append(f"[blue]🔗 NAD Link:[/blue] [dim]{metadata.nad_link}[/dim]")

        renderables.append("")

    def _format_page_content(self, panel_content: list[str], context: PageContext, highlight_term: str | None, show_links: bool, is_last: bool) -> None:
        """Render a single page: separator, text, optional links, spacing."""
        if show_links:
            panel_content.append(f"[dim]────── Page {context.page_number} ──────[/dim]")
        elif context.bildvisning_url:
            panel_content.append(f"[dim]────── Page {context.page_number} | [/dim][link]{context.bildvisning_url}[/link][dim] ──────[/dim]")
        else:
            panel_content.append(f"[dim]────── Page {context.page_number} ──────[/dim]")

        if context.full_text.strip():
            display_text = context.full_text
            if highlight_term:
                display_text = self.highlight_search_keyword(display_text, highlight_term)
            panel_content.append(f"[italic]{display_text}[/italic]")
        else:
            panel_content.append("[dim italic](Empty page - no transcribed text)[/dim italic]")

        if show_links:
            panel_content.append("\n[bold cyan]🔗 Links:[/bold cyan]")
            panel_content.append(f"     [dim]📝 ALTO XML:[/dim] [link]{context.alto_url}[/link]")
            if context.image_url:
                panel_content.append(f"     [dim]🖼️  Image:[/dim] [link]{context.image_url}[/link]")
            if context.bildvisning_url:
                panel_content.append(f"     [dim]👁️  Bildvisning:[/dim] [link]{context.bildvisning_url}[/link]")

        if not is_last:
            panel_content.append("")

    def format_browse_results(
        self,
        browse_result: BrowseResult,
        highlight_term: str | None = None,
        show_links: bool = False,
        show_success_message: bool = True,
    ) -> list[Any]:
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
        if not browse_result.contexts and browse_result.oai_metadata:
            return self._format_non_digitised_panel(browse_result)

        output: list[Any] = []

        if show_success_message and browse_result.contexts:
            output.append(f"[green]Successfully loaded {len(browse_result.contexts)} pages[/green]")

        # Group page contexts by reference code
        grouped_contexts: dict[str, list[PageContext]] = {}
        for context in browse_result.contexts:
            ref_code = context.reference_code
            if ref_code not in grouped_contexts:
                grouped_contexts[ref_code] = []
            grouped_contexts[ref_code].append(context)

        for ref_code, contexts in grouped_contexts.items():
            sorted_contexts = sorted(contexts, key=lambda c: c.page_number)
            renderables: list[Any] = []

            if browse_result.oai_metadata:
                self._format_group_metadata(renderables, browse_result.oai_metadata, ref_code)
            else:
                renderables.append(f"[bold blue]📄 Volume:[/bold blue] {ref_code}")
                renderables.append("")

            panel_content: list[str] = []
            for i, context in enumerate(sorted_contexts):
                self._format_page_content(panel_content, context, highlight_term, show_links, is_last=(i == len(sorted_contexts) - 1))

            renderables.extend(panel_content)

            panel_group = Group(*renderables)
            grouped_panel = Panel(
                panel_group,
                title=None,
                border_style="green",
                padding=(1, 1),
            )
            output.append("")
            output.append(grouped_panel)

        return output

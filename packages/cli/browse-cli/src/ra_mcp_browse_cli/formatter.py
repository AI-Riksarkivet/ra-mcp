"""
Rich console formatter for browse CLI output.
Creates actual Rich objects (Panels, Groups) for console display.
"""

import re
from typing import Any

from rich.console import Console, Group
from rich.panel import Panel

from ra_mcp_browse_lib.models import BrowseResult, PageContext


class RichConsoleFormatter:
    """Formatter that creates Rich objects for browse CLI display."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def highlight_search_keyword(self, text_content: str, search_keyword: str) -> str:
        """
        Highlight search keywords using Rich markup.
        First converts **text** markers from API to Rich highlighting.
        Then highlights the search keyword if no markers present.
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

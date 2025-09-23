"""
Refactored CLI commands using the shared business logic layer.
This eliminates code duplication with the MCP tools.
"""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core import (
    SearchOperations,
    UnifiedDisplayService,
    RichConsoleFormatter,
    SearchResultsAnalyzer,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MAX_DISPLAY,
    DEFAULT_MAX_PAGES
)

console = Console()


class RichDisplayAdapter:
    """
    Adapter that bridges between UnifiedDisplayService and Rich console output.
    Handles the Rich-specific formatting that can't be abstracted.
    """

    def __init__(self):
        self.display_service = UnifiedDisplayService(RichConsoleFormatter())
        self.analyzer = SearchResultsAnalyzer()

    def display_search_hits_rich(self, operation, max_display: int):
        """Display search hits using Rich tables (specific to CLI)."""
        if not operation.hits:
            console.print("[yellow]No search hits found.[/yellow]")
            return

        summary = self.analyzer.extract_search_summary(operation)
        grouped_hits = summary['grouped_hits']

        console.print(f"\n✓ Found {summary['page_hits_returned']} page-level hits across {summary['documents_returned']} documents")
        console.print("[dim]💡 Tips: Use --context to see full page transcriptions | Use 'browse' command to view specific reference codes[/dim]")

        table = Table(
            "Institution & Reference", "Content",
            title=f"Search Results for '{operation.keyword}'",
            show_lines=True,
            expand=True
        )

        # Display grouped results
        displayed_groups = 0
        for ref_code, ref_hits in grouped_hits.items():
            if displayed_groups >= max_display:
                break
            displayed_groups += 1

            # Take the first hit as representative for metadata
            first_hit = ref_hits[0]

            # Extract institution
            institution = ""
            if first_hit.archival_institution:
                institution = first_hit.archival_institution[0].get('caption', '') if first_hit.archival_institution else ""
            elif first_hit.hierarchy:
                institution = first_hit.hierarchy[0].get('caption', '') if first_hit.hierarchy else ""

            # Combine institution and reference with pages
            institution_and_ref = ""
            if institution:
                institution_and_ref = f"🏛️  {institution[:30] + '...' if len(institution) > 30 else institution}\n"

            # Format pages - list all pages, comma separated, with leading zeros trimmed
            pages = sorted(set(h.page_number for h in ref_hits))
            pages_trimmed = []
            for p in pages:
                trimmed = p.lstrip('0') or '0'  # Keep at least one zero if all zeros
                pages_trimmed.append(trimmed)
            pages_str = ",".join(pages_trimmed)

            institution_and_ref += f"📚 \"{ref_code}\" --page \"{pages_str}\""

            if first_hit.date:
                institution_and_ref += f"\n📅 [dim]{first_hit.date}[/dim]"

            # Create content column with title and snippets from different pages
            title_text = first_hit.title[:50] + '...' if len(first_hit.title) > 50 else first_hit.title
            content_parts = []

            # Add title
            if title_text and title_text.strip():
                content_parts.append(f"[bold blue]{title_text}[/bold blue]")
            else:
                content_parts.append(f"[bright_black]No title[/bright_black]")

            # Add snippets with page numbers
            for hit in ref_hits[:3]:  # Show max 3 snippets per reference
                snippet = hit.snippet_text[:150] + '...' if len(hit.snippet_text) > 150 else hit.snippet_text
                snippet = self.display_service.formatter.keyword_highlight(snippet, operation.keyword)
                content_parts.append(f"[dim]Page {hit.page_number}:[/dim] [italic]{snippet}[/italic]")

            if len(ref_hits) > 3:
                content_parts.append(f"[dim]...and {len(ref_hits) - 3} more pages with hits[/dim]")

            content = "\n".join(content_parts)

            table.add_row(institution_and_ref, content)

        console.print(table)

        # Show example browse command
        if grouped_hits:
            first_ref = next(iter(grouped_hits.keys()))
            first_group = grouped_hits[first_ref]
            pages = sorted(set(h.page_number for h in first_group))
            pages_trimmed = [p.lstrip('0') or '0' for p in pages[:5]]

            console.print(f"\n[dim]💡 Example: To view these hits, run:[/dim]")
            if len(pages_trimmed) == 1:
                console.print(f"[cyan]   ra browse \"{first_ref}\" --page {pages_trimmed[0]} --search-term \"{operation.keyword}\"[/cyan]")
            else:
                pages_str = ",".join(pages_trimmed)
                console.print(f"[cyan]   ra browse \"{first_ref}\" --page \"{pages_str}\" --search-term \"{operation.keyword}\"[/cyan]")

        # Count remaining groups
        total_groups = len(grouped_hits)
        if total_groups > displayed_groups:
            remaining_groups = total_groups - displayed_groups
            console.print(f"\n[dim]... and {remaining_groups} more documents[/dim]")

    def display_page_contexts_rich(self, operation, highlight_term: str = ""):
        """Display page contexts using Rich panels (specific to CLI)."""
        if not operation.contexts:
            console.print("[yellow]No page contexts found.[/yellow]")
            return

        console.print(f"\n[bold]Full Page Transcriptions ({len(operation.contexts)} pages):[/bold]")

        for context in operation.contexts:
            # Build page content
            page_content = []

            # Full transcribed text with keyword highlighting
            display_text = self.display_service.formatter.keyword_highlight(context.full_text, highlight_term)
            page_content.append(f"\n[bold magenta]📜 Full Transcription:[/bold magenta]")
            page_content.append(f"[italic]{display_text}[/italic]")

            # Links section
            page_content.append(f"\n[bold cyan]🔗 Links:[/bold cyan]")
            page_content.append(f"     [dim]📝 ALTO XML:[/dim] [link]{context.alto_url}[/link]")
            if context.image_url:
                page_content.append(f"     [dim]🖼️  Image:[/dim] [link]{context.image_url}[/link]")
            if context.bildvisning_url:
                page_content.append(f"     [dim]👁️  Bildvisning:[/dim] [link]{context.bildvisning_url}[/link]")

            panel_title = f"[cyan]Page {context.page_number}: {context.reference_code or 'Unknown Reference'}[/cyan]"
            console.print(Panel(
                "\n".join(page_content),
                title=panel_title,
                border_style="green",
                padding=(0, 1)
            ))


@click.command()
@click.argument('keyword')
@click.option('--max', 'max_results', type=int, default=DEFAULT_MAX_RESULTS, help='Maximum search results')
@click.option('--max-display', type=int, default=DEFAULT_MAX_DISPLAY, help='Maximum results to display')
@click.option('--context', is_flag=True, help='Show full page context for search hits')
@click.option('--max-pages', type=int, default=DEFAULT_MAX_PAGES, help='Maximum pages to load context for')
@click.option('--no-grouping', is_flag=True, help='Show pages individually instead of grouped by document (only with --context)')
def search(keyword: str, max_results: int, max_display: int, context: bool, max_pages: int, no_grouping: bool):
    """Search for keyword in transcribed materials.

    Fast search across all transcribed documents in Riksarkivet.
    Returns reference codes and page numbers containing the keyword.

    Examples:
        ra search "Stockholm"
        ra search "trolldom" --context --max-pages 5
        ra search "vasa" --context --no-grouping --max-pages 3
    """
    # Use shared business logic
    search_ops = SearchOperations()
    display_adapter = RichDisplayAdapter()

    console.print(f"[blue]Searching for '{keyword}' in transcribed materials...[/blue]")

    try:
        # Perform search using shared logic
        operation = search_ops.search_transcribed(
            keyword=keyword,
            max_results=max_results,
            show_context=context,
            max_pages_with_context=max_pages if context else 0
        )

        console.print(f"[green]Found {len(operation.hits)} page-level hits in {operation.total_hits} documents[/green]")

        if context and operation.hits:
            # For context display, use the unified display service with Rich panels
            console.print(f"[green]Successfully loaded context for {len(operation.hits)} pages[/green]")

            if not no_grouping:
                # Group display
                grouped_hits = display_adapter.analyzer.group_hits_by_document(operation.hits)
                console.print(f"\n[bold]Search Results Grouped by Document ({len(grouped_hits)} documents, {len(operation.hits)} pages):[/bold]")

                for doc_ref, doc_hits in grouped_hits.items():
                    doc_hits.sort(key=lambda h: int(h.page_number) if h.page_number.isdigit() else 0)

                    # Create document panel content
                    content = []
                    first_hit = doc_hits[0]
                    content.append(f"[bold blue]📄 Title:[/bold blue] {first_hit.title}")
                    content.append(f"[bold green]📄 Pages with hits:[/bold green] {', '.join(h.page_number for h in doc_hits)}")

                    if first_hit.date:
                        content.append(f"[bold blue]📅 Date:[/bold blue] {first_hit.date}")

                    for hit in doc_hits[:3]:
                        if hit.full_page_text:
                            display_text = display_adapter.display_service.formatter.keyword_highlight(hit.full_page_text[:300], keyword)
                            content.append(f"\n[bold cyan]Page {hit.page_number}:[/bold cyan]")
                            content.append(f"[italic]{display_text}{'...' if len(hit.full_page_text) > 300 else ''}[/italic]")

                    panel_title = f"[cyan]Document: {doc_ref} ({len(doc_hits)} pages)[/cyan]"
                    console.print(Panel(
                        "\n".join(content),
                        title=panel_title,
                        border_style="green",
                        padding=(0, 1)
                    ))
            else:
                # Individual page display
                console.print(f"\n[bold]Search Results with Full Page Context ({len(operation.hits)} pages):[/bold]")
                for hit in operation.hits:
                    if hit.full_page_text:
                        content = []
                        content.append(f"[bold blue]📄 Title:[/bold blue] {hit.title}")
                        if hit.date:
                            content.append(f"[bold blue]📅 Date:[/bold blue] {hit.date}")

                        display_text = display_adapter.display_service.formatter.keyword_highlight(hit.full_page_text, keyword)
                        content.append(f"\n[bold magenta]📜 Full Transcription:[/bold magenta]")
                        content.append(f"[italic]{display_text}[/italic]")

                        panel_title = f"[cyan]Hit: {hit.reference_code} - Page {hit.page_number}[/cyan]"
                        console.print(Panel(
                            "\n".join(content),
                            title=panel_title,
                            border_style="blue",
                            padding=(0, 1)
                        ))
        else:
            # Use Rich table display for non-context results
            display_adapter.display_search_hits_rich(operation, max_display)

    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        sys.exit(1)


@click.command()
@click.argument('reference_code')
@click.option('--pages', help='Page range to display (e.g., "1-10" or "5,7,9")')
@click.option('--page', help='Single page or page range to display (alias for --pages)')
@click.option('--search-term', help='Highlight this term in the text')
@click.option('--max-display', type=int, default=DEFAULT_MAX_DISPLAY, help='Maximum pages to display')
def browse(reference_code: str, pages: Optional[str], page: Optional[str], search_term: Optional[str], max_display: int):
    """Browse pages by reference code.

    You can specify pages using either --pages or --page (they work the same way).
    If both are provided, --page takes precedence.

    Examples:
        ra browse "SE/RA/123" --page 5
        ra browse "SE/RA/123" --pages "1-10"
        ra browse "SE/RA/123" --page "5,7,9"
    """
    # Use shared business logic
    search_ops = SearchOperations()
    display_adapter = RichDisplayAdapter()

    console.print(f"[blue]Looking up reference code: {reference_code}[/blue]")

    # Handle both --pages and --page options
    page_range = page if page is not None else pages

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Loading document information...", total=None)

            # Perform browse using shared logic
            operation = search_ops.browse_document(
                reference_code=reference_code,
                pages=page_range or "1-20",
                highlight_term=search_term,
                max_pages=max_display
            )

            progress.update(task, description=f"✓ Found PID: {operation.pid}")

        if not operation.contexts:
            console.print(f"[red]Could not load pages for {reference_code}[/red]")
            console.print("[yellow]Suggestions:[/yellow]")
            console.print("• Check the reference code format")
            console.print("• Try different page numbers")
            console.print("• The document might not have transcriptions")
            sys.exit(1)

        console.print(f"[green]Successfully loaded {len(operation.contexts)} pages[/green]")

        # Use Rich panel display
        display_adapter.display_page_contexts_rich(operation, search_term or "")

    except Exception as e:
        console.print(f"[red]Browse failed: {e}[/red]")
        sys.exit(1)


@click.command(name='show-pages')
@click.argument('keyword')
@click.option('--max-pages', type=int, default=DEFAULT_MAX_PAGES, help='Maximum pages to display with full context')
@click.option('--context-padding', type=int, default=1, help='Number of pages to include before and after each hit for context')
@click.option('--no-grouping', is_flag=True, help='Show pages individually instead of grouped by document')
def show_pages(keyword: str, max_pages: int, context_padding: int, no_grouping: bool):
    """Search for keyword and show the exact pages containing it with context.

    This combines search and browse - finds pages with the keyword then displays
    the full page transcriptions with the keyword highlighted, plus surrounding
    pages for context. Results are grouped by document by default for better context.

    Examples:
        ra show-pages "Stockholm" --max-pages 5
        ra show-pages "trolldom" --no-grouping
        ra show-pages "vasa" --context-padding 2
    """
    # Use shared business logic
    search_ops = SearchOperations()
    display_adapter = RichDisplayAdapter()

    console.print(f"[blue]Searching for '{keyword}' to find exact pages...[/blue]")

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Searching and loading contexts...", total=None)

            # Perform show-pages using shared logic
            search_op, enriched_hits = search_ops.show_pages_with_context(
                keyword=keyword,
                max_pages=max_pages,
                context_padding=context_padding,
                search_limit=max(max_pages * 3, 50)
            )

            progress.update(task, description=f"✓ Found {len(enriched_hits)} pages with context")

        if not enriched_hits:
            console.print("[yellow]No pages found containing the keyword.[/yellow]")
            return

        console.print(f"\n[green]Found {len(search_op.hits)} pages containing '{keyword}'[/green]")
        console.print(f"[blue]Showing {len(enriched_hits)} pages including context padding (+/- {context_padding} pages)...[/blue]")

        # Use the unified display service format but render with Rich
        result_text = display_adapter.display_service.format_show_pages_results(
            search_op, enriched_hits, no_grouping
        )

        # For now, just print the formatted text - we could enhance this further with Rich panels
        console.print(result_text)

    except Exception as e:
        console.print(f"[red]Show pages failed: {e}[/red]")
        sys.exit(1)


@click.command()
@click.option('--port', type=int, default=None, help='Port for HTTP/SSE transport (enables HTTP mode)')
@click.option('--host', default='localhost', help='Host for HTTP transport')
def serve(port: Optional[int], host: str):
    """Start the MCP server.

    Examples:
        ra serve                    # Start with stdio transport
        ra serve --port 8000        # Start with HTTP/SSE transport on port 8000
    """
    if port:
        console.print(f"[blue]Starting MCP server with HTTP/SSE transport on {host}:{port}[/blue]")
        # Import and run the HTTP server
        from ..server import main as server_main
        import sys

        # Set up sys.argv for the server
        original_argv = sys.argv
        sys.argv = ['ra-mcp-server', '--http', '--port', str(port), '--host', host]

        try:
            server_main()
        finally:
            sys.argv = original_argv
    else:
        console.print("[blue]Starting MCP server with stdio transport[/blue]")
        # Import and run the stdio server
        from ..server import main as server_main
        import sys

        # Set up sys.argv for the server
        original_argv = sys.argv
        sys.argv = ['ra-mcp-server']

        try:
            server_main()
        finally:
            sys.argv = original_argv
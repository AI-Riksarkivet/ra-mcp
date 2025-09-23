"""
CLI commands for ra-mcp.
"""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core import (
    SearchAPI,
    SearchEnrichmentService,
    PageContextService,
    IIIFClient,
    OAIPMHClient,
    HTTPClient,
    parse_page_range,
    SEARCH_API_BASE_URL,
    REQUEST_TIMEOUT,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MAX_DISPLAY,
    DEFAULT_MAX_PAGES
)

console = Console()


class RichDisplayService:
    """Display service with rich console output (like the original tools/ra.py)."""

    @staticmethod
    def keyword_highlight(text: str, keyword: str) -> str:
        """Highlight keyword in text."""
        if not keyword:
            return text
        import re
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(lambda m: f"[bold yellow underline]{m.group()}[/bold yellow underline]", text)

    def display_search_hits(self, hits, keyword: str, max_display: int = DEFAULT_MAX_DISPLAY):
        """Display search hits in a table, grouped by reference code."""
        if not hits:
            console.print("[yellow]No search hits found.[/yellow]")
            return

        # Group hits by reference code
        from collections import OrderedDict
        grouped_hits = OrderedDict()
        for hit in hits:
            ref_code = hit.reference_code or hit.pid
            if ref_code not in grouped_hits:
                grouped_hits[ref_code] = []
            grouped_hits[ref_code].append(hit)

        console.print(f"\n✓ Found {len(hits)} page-level hits across {len(grouped_hits)} documents")
        console.print("[dim]💡 Tips: Use --context to see full page transcriptions | Use 'browse' command to view specific reference codes[/dim]")

        table = Table(
            "Institution & Reference", "Content",
            title=f"Search Results for '{keyword}'",
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
                snippet = self.keyword_highlight(snippet, keyword)
                content_parts.append(f"[dim]Page {hit.page_number}:[/dim] [italic]{snippet}[/italic]")

            if len(ref_hits) > 3:
                content_parts.append(f"[dim]...and {len(ref_hits) - 3} more pages with hits[/dim]")

            content = "\n".join(content_parts)

            table.add_row(institution_and_ref, content)

        console.print(table)

        # Show example browse command with actual reference from first group
        if grouped_hits:
            first_ref = next(iter(grouped_hits.keys()))
            first_group = grouped_hits[first_ref]
            pages = sorted(set(h.page_number for h in first_group))

            # Trim leading zeros from page numbers and limit to max 5 pages for example
            pages_trimmed = [p.lstrip('0') or '0' for p in pages[:5]]  # Take first 5 pages max

            console.print(f"\n[dim]💡 Example: To view these hits, run:[/dim]")
            if len(pages_trimmed) == 1:
                console.print(f"[cyan]   ra browse \"{first_ref}\" --page {pages_trimmed[0]} --search-term \"{keyword}\"[/cyan]")
            else:
                pages_str = ",".join(pages_trimmed)
                if len(pages) > 5:
                    console.print(f"[cyan]   ra browse \"{first_ref}\" --page \"{pages_str}\" --search-term \"{keyword}\"[/cyan]")
                    console.print(f"[dim]   (Showing first 5 of {len(pages)} pages with hits)[/dim]")
                else:
                    console.print(f"[cyan]   ra browse \"{first_ref}\" --page \"{pages_str}\" --search-term \"{keyword}\"[/cyan]")

        # Count remaining groups instead of hits
        total_groups = len(grouped_hits)
        if total_groups > displayed_groups:
            remaining_groups = total_groups - displayed_groups
            total_remaining_hits = sum(len(h) for _, h in list(grouped_hits.items())[displayed_groups:])
            console.print(f"\n[dim]... and {remaining_groups} more documents with {total_remaining_hits} hits[/dim]")
            console.print(f"[dim]Options: --max-display N to show more | --context for full pages | 'browse REFERENCE' to view specific documents[/dim]")

    def display_page_contexts(self, contexts, keyword: str, reference_code: str = ""):
        """Display full page contexts with keyword highlighting."""
        if not contexts:
            console.print("[yellow]No page contexts found.[/yellow]")
            return

        console.print(f"\n[bold]Full Page Transcriptions ({len(contexts)} pages):[/bold]")

        for context in contexts:
            page_content = self._build_page_content(context, keyword, reference_code)
            panel_title = f"[cyan]Page {context.page_number}: {context.reference_code or 'Unknown Reference'}[/cyan]"
            console.print(Panel(
                "\n".join(page_content),
                title=panel_title,
                border_style="green",
                padding=(0, 1)
            ))

    def _build_page_content(self, context, keyword: str, reference_code: str):
        """Build content for a page panel."""
        page_content = []

        # Full transcribed text with keyword highlighting
        display_text = self.keyword_highlight(context.full_text, keyword)
        page_content.append(f"\n[bold magenta]📜 Full Transcription:[/bold magenta]")
        page_content.append(f"[italic]{display_text}[/italic]")

        # Links section
        page_content.append(f"\n[bold cyan]🔗 Links:[/bold cyan]")
        page_content.append(f"     [dim]📝 ALTO XML:[/dim] [link]{context.alto_url}[/link]")
        if context.image_url:
            page_content.append(f"     [dim]🖼️  Image:[/dim] [link]{context.image_url}[/link]")
        if context.bildvisning_url:
            page_content.append(f"     [dim]👁️  Bildvisning:[/dim] [link]{context.bildvisning_url}[/link]")

        return page_content


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
    search_api = SearchAPI()
    display_service = RichDisplayService()

    console.print(f"[blue]Searching for '{keyword}' in transcribed materials...[/blue]")

    try:
        hits, total_hits = search_api.search_transcribed_text(keyword, max_results)
        console.print(f"[green]Found {len(hits)} page-level hits in {total_hits} documents[/green]")

        if context and hits:
            enrichment_service = SearchEnrichmentService()
            console.print(f"[blue]Fetching full page context for up to {max_pages} pages...[/blue]")

            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task("Loading page contexts...", total=min(len(hits), max_pages))
                enriched_hits = enrichment_service.enrich_hits_with_context(hits, max_pages, keyword)
                progress.update(task, completed=min(len(hits), max_pages))

            # For context display, we'll show a simplified version
            console.print(f"[green]Successfully loaded context for {len(enriched_hits)} pages[/green]")

            # Group hits for display if not no-grouping
            if not no_grouping:
                from collections import defaultdict
                grouped_hits = defaultdict(list)
                for hit in enriched_hits:
                    if hit.full_page_text:
                        key = hit.reference_code or hit.pid
                        grouped_hits[key].append(hit)

                console.print(f"\n[bold]Search Results Grouped by Document ({len(grouped_hits)} documents, {len(enriched_hits)} pages):[/bold]")

                for doc_ref, doc_hits in grouped_hits.items():
                    # Sort pages by page number
                    doc_hits.sort(key=lambda h: int(h.page_number) if h.page_number.isdigit() else 0)

                    # Create simplified document display
                    first_hit = doc_hits[0]
                    content = []
                    content.append(f"[bold blue]📄 Title:[/bold blue] {first_hit.title}")
                    content.append(f"[bold green]📄 Pages with hits:[/bold green] {', '.join(h.page_number for h in doc_hits)}")

                    if first_hit.date:
                        content.append(f"[bold blue]📅 Date:[/bold blue] {first_hit.date}")

                    for hit in doc_hits[:3]:  # Show first 3 pages
                        if hit.full_page_text:
                            display_text = display_service.keyword_highlight(hit.full_page_text[:300], keyword)
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
                console.print(f"\n[bold]Search Results with Full Page Context ({len(enriched_hits)} pages):[/bold]")
                for hit in enriched_hits:
                    if hit.full_page_text:
                        content = []
                        content.append(f"[bold blue]📄 Title:[/bold blue] {hit.title}")
                        if hit.date:
                            content.append(f"[bold blue]📅 Date:[/bold blue] {hit.date}")

                        display_text = display_service.keyword_highlight(hit.full_page_text, keyword)
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
            display_service.display_search_hits(hits, keyword, max_display)

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
    console.print(f"[blue]Looking up reference code: {reference_code}[/blue]")

    # Handle both --pages and --page options (--page takes precedence if both are provided)
    page_range = page if page is not None else pages

    # Try search API first
    session = HTTPClient.create_session()
    pid = None

    try:
        params = {'reference_code': reference_code, 'only_digitised_materials': 'true', 'max': 1}
        response = session.get(SEARCH_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if data.get('items'):
            pid = data['items'][0].get('id')
            console.print(f"[green]Found PID via search: {pid}[/green]")
    except Exception as e:
        console.print(f"[yellow]Search API lookup failed: {e}[/yellow]")

    # Fall back to OAI-PMH
    if not pid:
        console.print(f"[blue]Trying OAI-PMH lookup...[/blue]")
        oai_client = OAIPMHClient()
        try:
            pid = oai_client.extract_pid(reference_code)
            if pid:
                console.print(f"[green]Found PID via OAI-PMH: {pid}[/green]")
            else:
                console.print(f"[red]Could not extract PID for {reference_code}[/red]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error getting OAI-PMH record: {e}[/red]")
            sys.exit(1)

    # Get manifest and load pages
    iiif_client = IIIFClient()
    collection_info = iiif_client.explore_collection(pid)

    manifest_id = pid
    if collection_info and collection_info.get('manifests'):
        manifest_id = collection_info['manifests'][0]['id']
        console.print(f"[green]Found manifest: {manifest_id}[/green]")

    selected_pages = parse_page_range(page_range)
    console.print(f"[blue]Loading {len(selected_pages[:max_display])} pages...[/blue]")

    # Load page contexts
    page_service = PageContextService()
    display_service = RichDisplayService()
    contexts = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Loading page contexts...", total=len(selected_pages[:max_display]))

        for page_num in selected_pages[:max_display]:
            progress.update(task, description=f"Loading page {page_num}...")
            context = page_service.get_page_context(manifest_id, str(page_num), reference_code, search_term)
            if context:
                contexts.append(context)
                progress.update(task, description=f"✓ Loaded page {page_num}")
            else:
                progress.update(task, description=f"✗ Failed to load page {page_num}")
            progress.advance(task)

    display_service.display_page_contexts(contexts, search_term or "", reference_code)
    console.print(f"\n[green]Successfully loaded {len(contexts)} pages[/green]")


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
    # Step 1: Search for the keyword
    search_limit = max(max_pages * 3, 50)  # Get more results to have options
    console.print(f"[blue]Searching for '{keyword}' to find exact pages...[/blue]")

    search_api = SearchAPI()
    try:
        hits, total_hits = search_api.search_transcribed_text(keyword, search_limit)
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        sys.exit(1)

    if not hits:
        console.print("[yellow]No pages found containing the keyword.[/yellow]")
        return

    # Step 2: Show basic search results first
    console.print(f"\n[green]Found {len(hits)} pages containing '{keyword}'[/green]")

    # Limit to max_pages for detailed display
    display_hits = hits[:max_pages]
    console.print(f"[blue]Showing full context for first {len(display_hits)} pages...[/blue]")

    # Step 3: Expand hits with context padding and enrich with full page context
    enrichment_service = SearchEnrichmentService()
    expanded_hits = enrichment_service.expand_hits_with_context_padding(display_hits, context_padding)
    console.print(f"[blue]Expanded to {len(expanded_hits)} pages including context padding (+/- {context_padding} pages)...[/blue]")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Loading page contexts...", total=len(expanded_hits))
        enriched_hits = enrichment_service.enrich_hits_with_context(expanded_hits, len(expanded_hits), keyword)
        progress.update(task, completed=len(expanded_hits))

    # Step 4: Display results (grouped by document by default)
    display_service = RichDisplayService()
    if enriched_hits:
        # Simplified display for show-pages
        if not no_grouping:
            from collections import defaultdict
            grouped_hits = defaultdict(list)
            for hit in enriched_hits:
                if hit.full_page_text:
                    key = hit.reference_code or hit.pid
                    grouped_hits[key].append(hit)

            console.print(f"\n[bold]Pages with Context Grouped by Document ({len(grouped_hits)} documents, {len(enriched_hits)} pages):[/bold]")

            for doc_ref, doc_hits in grouped_hits.items():
                doc_hits.sort(key=lambda h: int(h.page_number) if h.page_number.isdigit() else 0)

                content = []
                first_hit = doc_hits[0]
                content.append(f"[bold blue]📄 Title:[/bold blue] {first_hit.title}")
                content.append(f"[bold green]📄 Pages:[/bold green] {', '.join(h.page_number for h in doc_hits)}")

                if first_hit.date:
                    content.append(f"[bold blue]📅 Date:[/bold blue] {first_hit.date}")

                # Add each page's content
                for i, hit in enumerate(doc_hits, 1):
                    is_search_hit = hit.snippet_text != "[Context page - no search hit]"
                    page_marker = "🎯" if is_search_hit else "📄"
                    page_type = "[bold yellow]SEARCH HIT[/bold yellow]" if is_search_hit else "[dim]context[/dim]"

                    content.append(f"\n[bold cyan]── {page_marker} Page {hit.page_number} ({page_type}) ──[/bold cyan]")

                    display_text = hit.full_page_text or ""
                    if keyword and is_search_hit and display_text:
                        display_text = display_service.keyword_highlight(display_text, keyword)

                    if display_text:
                        content.append(f"[italic]{display_text}[/italic]")
                    else:
                        content.append(f"[dim italic]No text content available for this page[/dim italic]")

                panel_title = f"[cyan]Document: {doc_ref} ({len(doc_hits)} pages)[/cyan]"
                console.print(Panel(
                    "\n".join(content),
                    title=panel_title,
                    border_style="green",
                    padding=(0, 1)
                ))
        else:
            # Individual page display
            console.print(f"\n[bold]Search Results with Full Page Context ({len(enriched_hits)} pages):[/bold]")
            for hit in enriched_hits:
                if hit.full_page_text:
                    content = []
                    content.append(f"[bold blue]📄 Title:[/bold blue] {hit.title}")
                    if hit.date:
                        content.append(f"[bold blue]📅 Date:[/bold blue] {hit.date}")

                    is_search_hit = hit.snippet_text != "[Context page - no search hit]"
                    if is_search_hit:
                        display_text = display_service.keyword_highlight(hit.full_page_text, keyword)
                    else:
                        display_text = hit.full_page_text

                    content.append(f"\n[bold magenta]📜 Full Transcription:[/bold magenta]")
                    content.append(f"[italic]{display_text}[/italic]")

                    page_type = " (SEARCH HIT)" if is_search_hit else " (context)"
                    panel_title = f"[cyan]Hit: {hit.reference_code} - Page {hit.page_number}{page_type}[/cyan]"
                    console.print(Panel(
                        "\n".join(content),
                        title=panel_title,
                        border_style="blue" if is_search_hit else "dim",
                        padding=(0, 1)
                    ))
    else:
        console.print("[red]No page transcriptions could be loaded.[/red]")


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
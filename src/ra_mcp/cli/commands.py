"""
CLI commands for Riksarkivet MCP server.
"""

from typing import Optional, Annotated
import os

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..services import SearchOperations, analysis
from ..services.display_service import DisplayService
from ..formatters import RichConsoleFormatter
from ..utils.http_client import HTTPClient, default_http_client
from ..config import DEFAULT_MAX_RESULTS, DEFAULT_MAX_DISPLAY, DEFAULT_MAX_PAGES
from ..models import SearchOperation, BrowseOperation, PageContext, DocumentMetadata

console = Console()
app = typer.Typer()


def get_http_client(enable_logging: bool) -> HTTPClient:
    """Get HTTP client with optional logging enabled."""
    if enable_logging:
        os.environ["RA_MCP_LOG_API"] = "1"
        return HTTPClient()
    return default_http_client


def show_logging_status(enabled: bool) -> None:
    """Display logging status message."""
    if enabled:
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")


def display_search_summary(search_result: SearchOperation, keyword: str) -> None:
    """Display search result summary."""
    console.print(f"[green]Found {len(search_result.hits)} page-level hits in {search_result.total_hits} documents[/green]")


def display_context_results(
    search_result: SearchOperation,
    display_service: DisplayService,
    keyword: str,
    show_links: bool = False,
) -> None:
    """Display search results with full context using unified page display."""

    # Sort hits by reference code and page number for better organization
    sorted_hits = sorted(search_result.hits, key=lambda hit: (hit.reference_code, int(hit.page_number)))

    # Convert SearchHits to PageContext format and group by reference code
    # Use a set to track seen pages and avoid duplicates
    grouped_contexts = {}
    seen_pages = set()

    for hit in sorted_hits:
        if hit.full_page_text:
            ref_code = hit.reference_code
            page_key = f"{ref_code}_{hit.page_number}"

            # Skip if we've already seen this exact page
            if page_key in seen_pages:
                continue

            seen_pages.add(page_key)

            if ref_code not in grouped_contexts:
                grouped_contexts[ref_code] = []

            page_context = PageContext(
                page_number=int(hit.page_number),
                page_id=page_key,
                reference_code=hit.reference_code,
                full_text=hit.full_page_text,
                alto_url=hit.alto_url or "",
                image_url=hit.image_url or "",
                bildvisning_url=hit.bildvisning_url or "",
            )
            grouped_contexts[ref_code].append(page_context)

    # Calculate total unique pages after deduplication
    total_unique_pages = sum(len(contexts) for contexts in grouped_contexts.values())
    console.print(f"[green]Successfully loaded {total_unique_pages} pages[/green]")

    # Display each document separately with its own metadata
    for ref_code, contexts in grouped_contexts.items():
        # Get metadata for this specific document
        representative_hit = next(hit for hit in sorted_hits if hit.reference_code == ref_code and hit.full_page_text)

        document_metadata = DocumentMetadata(
            title=representative_hit.title,
            hierarchy=representative_hit.hierarchy,
            archival_institution=representative_hit.archival_institution,
            date=representative_hit.date,
            note=representative_hit.note,
            collection_url=representative_hit.collection_url,
            manifest_url=representative_hit.manifest_url,
        )

        # Create a mock browse result for this document
        mock_browse = BrowseOperation(
            contexts=contexts,
            reference_code=ref_code,
            pages_requested="context",
            pid=None,
            document_metadata=document_metadata,
        )

        # Display this document
        display_browse_results(mock_browse, display_service, keyword, show_links, False)  # Don't show success message


def display_table_results(
    search_result: SearchOperation,
    display_service: DisplayService,
    max_display: int,
    keyword: str,
) -> None:
    """Display search results in table format."""
    formatted_table = display_service.format_search_results(search_result, max_display, False)

    if not formatted_table:
        return

    # Get search summary and display it
    summary = analysis.extract_search_summary(search_result)
    summary_lines = display_service.formatter.format_search_summary(summary)
    for line in summary_lines:
        console.print(line)

    # Display the table
    if isinstance(formatted_table, str):
        console.print(formatted_table)
    else:
        console.print(formatted_table)
        # Display browse examples and remaining documents inline
        grouped_hits = summary.grouped_hits
        example_lines = display_service.formatter.format_browse_example(grouped_hits, keyword)
        for line in example_lines:
            console.print(line)

        total_groups = len(grouped_hits)
        remaining_message = display_service.formatter.format_remaining_documents(total_groups, max_display)
        if remaining_message:
            console.print(remaining_message)


def perform_search_with_progress(
    search_operations,
    keyword: str,
    max_results: int,
    browse: bool,
    max_pages: int,
    context_padding: int,
    max_hits_per_document: Optional[int],
):
    """Execute the search operation with enhanced progress indicators."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Phase 1: Initial search across all volumes
        search_task = progress.add_task(f"Searching for '{keyword}' across all transcribed volumes...", total=None)

        search_result = search_operations.search_transcribed(
            keyword=keyword,
            max_results=max_results,
            show_context=False,  # First get basic results
            max_pages_with_context=0,
            context_padding=0,
            max_hits_per_document=max_hits_per_document,
        )

        # Update with detailed results
        hits_count = len(search_result.hits)
        docs_count = search_result.total_hits
        progress.update(
            search_task,
            description=f"✓ Found {hits_count} page hits across {docs_count} volumes",
        )

        # Phase 2: Load full page content if in browse mode
        if browse and search_result.hits and max_pages > 0:
            limited_hits = min(hits_count, max_pages)

            # Group hits by volume to show more specific progress
            from collections import defaultdict

            hits_by_volume = defaultdict(list)
            for hit in search_result.hits[:max_pages]:
                hits_by_volume[hit.reference_code].append(hit)

            volume_count = len(hits_by_volume)
            context_task = progress.add_task(
                f"Loading ALTO transcriptions from {volume_count} volumes ({limited_hits} pages)...",
                total=None,
            )

            # Show which volumes are being processed
            volume_names = list(hits_by_volume.keys())[:3]  # Show first 3 volumes
            if len(volume_names) > 1:
                if volume_count > 3:
                    progress.update(
                        context_task,
                        description=f"Loading from: {volume_names[0]}, {volume_names[1]}, and {volume_count - 2} more...",
                    )
                else:
                    progress.update(
                        context_task,
                        description=f"Loading from: {', '.join(volume_names)}",
                    )
            elif volume_names:
                progress.update(context_task, description=f"Loading ALTO from: {volume_names[0]}")

            # Re-run with context loading
            search_result = search_operations.search_transcribed(
                keyword=keyword,
                max_results=max_results,
                show_context=True,
                max_pages_with_context=max_pages,
                context_padding=context_padding,
                max_hits_per_document=max_hits_per_document,
            )

            # Count successfully loaded pages with context
            enriched_count = sum(1 for hit in search_result.hits if hit.full_page_text)
            if context_padding > 0:
                progress.update(
                    context_task,
                    description=f"✓ Loaded {enriched_count} pages with {context_padding}-page context padding from {volume_count} volumes",
                )
            else:
                progress.update(
                    context_task,
                    description=f"✓ Loaded ALTO transcriptions for {enriched_count} pages from {volume_count} volumes",
                )

    return search_result


@app.command()
def search(
    keyword: Annotated[str, typer.Argument(help="Keyword to search for")],
    max_results: Annotated[int, typer.Option("--max", help="Maximum search results")] = DEFAULT_MAX_RESULTS,
    max_display: Annotated[int, typer.Option(help="Maximum results to display")] = DEFAULT_MAX_DISPLAY,
    browse: Annotated[
        bool,
        typer.Option(
            "--browse",
            help="Show full page content for search hits (browse-style display)",
        ),
    ] = False,
    max_pages: Annotated[int, typer.Option(help="Maximum pages to load context for")] = DEFAULT_MAX_PAGES,
    context_padding: Annotated[
        int,
        typer.Option(help="Number of pages to include before and after each hit for context (only with --browse)"),
    ] = 0,
    max_hits_per_document: Annotated[
        Optional[int],
        typer.Option(
            "--max-hits-per-vol",
            help="Maximum number of hits to return per volume (useful for searching across many volumes)",
        ),
    ] = 3,
    log: Annotated[bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")] = False,
    show_links: Annotated[
        bool,
        typer.Option(
            "--show-links",
            help="Display ALTO XML, Image, and Bildvisning links (only with --browse)",
        ),
    ] = False,
):
    """Search for keyword in transcribed materials.

    Fast search across all transcribed documents in Riksarkivet.
    Returns reference codes and page numbers containing the keyword.
    Use --browse to see full page transcriptions with optional context padding.

    By default, returns up to 3 hits per volume. Use --max-hits-per-vol to adjust.

    Examples:
        ra search "Stockholm"                                    # Basic search (3 hits per volume)
        ra search "trolldom" --browse --max-pages 5             # Browse with 3 hits per volume
        ra search "vasa" --browse --context-padding 2           # With surrounding pages
        ra search "Stockholm" --max-hits-per-vol 2              # Max 2 hits per volume
        ra search "Stockholm" --browse --max-hits-per-vol 5     # Browse with 5 hits per volume
        ra search "Stockholm" --max 100 --max-hits-per-vol 1    # Many volumes, 1 hit each
        ra search "Stockholm" --log                             # With API logging
    """
    http_client = get_http_client(log)
    search_operations = SearchOperations(http_client=http_client)
    display_service = DisplayService(formatter=RichConsoleFormatter(console))

    show_logging_status(log)

    try:
        # Use the specified max_hits_per_document value (defaults to 3)
        effective_max_hits_per_doc = max_hits_per_document

        search_result = perform_search_with_progress(
            search_operations,
            keyword,
            max_results,
            browse,
            max_pages,
            context_padding,
            effective_max_hits_per_doc,
        )

        if browse and search_result.hits:
            display_context_results(search_result, display_service, keyword, show_links)
        else:
            display_table_results(search_result, display_service, max_display, keyword)

    except Exception as error:
        console.print(f"[red]Search failed: {error}[/red]")
        raise typer.Exit(code=1)


def display_browse_header(reference_code: str) -> None:
    """Display browse operation header."""
    console.print(f"[blue]Looking up reference code: {reference_code}[/blue]")


def load_document_with_progress(
    search_operations,
    reference_code: str,
    pages: str,
    search_term: Optional[str],
    max_display: int,
):
    """Load document with progress indicator."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        loading_task = progress.add_task("Loading document information...", total=None)

        browse_result = search_operations.browse_document(
            reference_code=reference_code,
            pages=pages,
            highlight_term=search_term,
            max_pages=max_display,
        )

        progress.update(loading_task, description=f"✓ Found PID: {browse_result.pid}")

    return browse_result


def display_browse_error(reference_code: str) -> None:
    """Display error message for failed browse operation."""
    console.print(f"[red]Could not load pages for {reference_code}[/red]")
    console.print("[yellow]Suggestions:[/yellow]")
    console.print("• Check the reference code format")
    console.print("• Try different page numbers")
    console.print("• The document might not have transcriptions")


def display_browse_results(
    browse_result,
    display_service,
    search_term: Optional[str],
    show_links: bool = False,
    show_success_message: bool = True,
) -> None:
    """Display successful browse results grouped by reference code."""
    if show_success_message:
        console.print(f"[green]Successfully loaded {len(browse_result.contexts)} pages[/green]")

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

        # Create a single grouped panel for all pages in this document

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
                        # Replace newlines with spaces to keep hierarchy on single lines
                        caption = caption.replace("\n", " ").strip()

                        if i == 0:
                            # Root level
                            right_content.append(f"📁 {caption}")
                        elif i == len(hierarchy) - 1:
                            # Last item
                            indent = "  " * i
                            right_content.append(f"{indent}└── 📄 {caption}")
                        else:
                            # Middle items
                            indent = "  " * i
                            right_content.append(f"{indent}├── 📁 {caption}")

            # Create clean two-column layout using Rich Table
            if right_content:
                # Create table with two columns
                metadata_table = Table.grid(padding=(0, 2))  # Add some padding between columns
                metadata_table.add_column(justify="left", ratio=1)  # Left column for basic info
                metadata_table.add_column(justify="left", ratio=1)  # Right column for hierarchy

                left_text = "\n".join(left_content)
                right_text = "\n".join(right_content)

                metadata_table.add_row(left_text, right_text)
                renderables.append(metadata_table)
            else:
                # Fall back to single column if no hierarchy
                renderables.append("\n".join(left_content))

            # Display note on its own row if available
            if metadata.note:
                renderables.append(f"[blue]📝 Note:[/blue] {metadata.note}")

            # Add spacing after metadata
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
            if search_term:
                # Use the proper highlighting method which handles case-insensitive matching
                display_text = display_service.formatter.highlight_search_keyword(display_text, search_term)
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

        # Create the grouped panel using Rich Group to combine metadata and page content
        from rich.console import Group

        panel_group = Group(*renderables)

        grouped_panel = Panel(
            panel_group,
            title=None,
            border_style="green",
            padding=(1, 1),
        )
        console.print("")  # Add spacing before the panel
        console.print(grouped_panel)


@app.command()
def browse(
    reference_code: Annotated[str, typer.Argument(help="Reference code of the document")],
    pages: Annotated[
        Optional[str],
        typer.Option(help='Page range to display (e.g., "1-10" or "5,7,9")'),
    ] = None,
    page: Annotated[
        Optional[str],
        typer.Option(help="Single page or page range to display (alias for --pages)"),
    ] = None,
    search_term: Annotated[Optional[str], typer.Option(help="Highlight this term in the text")] = None,
    max_display: Annotated[int, typer.Option(help="Maximum pages to display")] = DEFAULT_MAX_DISPLAY,
    log: Annotated[bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")] = False,
    show_links: Annotated[
        bool,
        typer.Option("--show-links", help="Display ALTO XML, Image, and Bildvisning links"),
    ] = False,
):
    """Browse pages by reference code.

    You can specify pages using either --pages or --page (they work the same way).
    If both are provided, --page takes precedence.

    Examples:
        ra browse "SE/RA/123" --page 5
        ra browse "SE/RA/123" --pages "1-10"
        ra browse "SE/RA/123" --page "5,7,9"
        ra browse "SE/RA/123" --page 1 --log      # With API logging
    """
    http_client = get_http_client(log)
    search_operations = SearchOperations(http_client=http_client)
    display_service = DisplayService(formatter=RichConsoleFormatter(console))

    display_browse_header(reference_code)
    show_logging_status(log)

    requested_pages = page if page is not None else pages

    try:
        browse_result = load_document_with_progress(
            search_operations,
            reference_code,
            requested_pages or "1-20",
            search_term,
            max_display,
        )

        if not browse_result.contexts:
            display_browse_error(reference_code)
            raise typer.Exit(code=1)

        display_browse_results(browse_result, display_service, search_term, show_links)

    except Exception as error:
        console.print(f"[red]Browse failed: {error}[/red]")
        raise typer.Exit(code=1)


def start_stdio_server() -> None:
    """Start MCP server with stdio transport."""
    console.print("[blue]Starting MCP server with stdio transport[/blue]")
    from ..server import main as server_main
    import sys

    original_argv = sys.argv
    sys.argv = ["ra-mcp-server"]

    try:
        server_main()
    finally:
        sys.argv = original_argv


def start_http_server(host: str, port: int) -> None:
    """Start MCP server with HTTP/SSE transport."""
    console.print(f"[blue]Starting MCP server with HTTP/SSE transport on {host}:{port}[/blue]")
    from ..server import main as server_main
    import sys

    original_argv = sys.argv
    sys.argv = ["ra-mcp-server", "--http", "--port", str(port), "--host", host]

    try:
        server_main()
    finally:
        sys.argv = original_argv


@app.command()
def serve(
    port: Annotated[
        Optional[int],
        typer.Option(help="Port for HTTP/SSE transport (enables HTTP mode)"),
    ] = None,
    host: Annotated[str, typer.Option(help="Host for HTTP transport")] = "localhost",
    log: Annotated[bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")] = False,
):
    """Start the MCP server.

    Examples:
        ra serve                    # Start with stdio transport
        ra serve --port 8000        # Start with HTTP/SSE transport on port 8000
        ra serve --port 8000 --log  # Start with API logging enabled
    """
    if log:
        os.environ["RA_MCP_LOG_API"] = "1"
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")

    if port:
        start_http_server(host, port)
    else:
        start_stdio_server()


@app.callback()
def main_callback():
    """
    Riksarkivet MCP Server and CLI Tools.

    Search and browse transcribed historical documents from the Swedish National Archives.
    """
    pass

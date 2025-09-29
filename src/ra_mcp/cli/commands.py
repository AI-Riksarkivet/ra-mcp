"""
CLI commands for Riksarkivet MCP server.
"""

from typing import Optional, Annotated
import os

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..services import SearchOperations
from ..services.cli_display_service import CLIDisplayService
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
    console.print(
        f"[green]Found {len(search_result.hits)} page-level hits in {search_result.total_hits} documents[/green]"
    )


def display_context_results(
    search_result: SearchOperation, display_service: CLIDisplayService, keyword: str
) -> None:
    """Display search results with full context using unified page display."""

    # Sort hits by reference code and page number for better organization
    sorted_hits = sorted(
        search_result.hits, key=lambda hit: (hit.reference_code, int(hit.page_number))
    )

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
    console.print(
        f"[green]Successfully loaded {total_unique_pages} pages[/green]"
    )

    # Display each document separately with its own metadata
    for ref_code, contexts in grouped_contexts.items():
        # Get metadata for this specific document
        representative_hit = next(
            hit for hit in sorted_hits
            if hit.reference_code == ref_code and hit.full_page_text
        )

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
        display_browse_results(mock_browse, display_service, keyword, False, False)  # Don't show links or success message


def display_table_results(
    search_result: SearchOperation,
    display_service: CLIDisplayService,
    max_display: int,
    keyword: str,
) -> None:
    """Display search results in table format."""
    formatted_table = display_service.format_search_results(
        search_result, max_display, False
    )

    if not formatted_table:
        return

    # Get search summary and display it
    summary = display_service.get_search_summary(search_result)
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
        example_lines = display_service.formatter.format_browse_example(
            grouped_hits, keyword
        )
        for line in example_lines:
            console.print(line)

        total_groups = len(grouped_hits)
        remaining_message = display_service.formatter.format_remaining_documents(
            total_groups, max_display
        )
        if remaining_message:
            console.print(remaining_message)


def perform_search(
    search_operations,
    keyword: str,
    max_results: int,
    browse: bool,
    max_pages: int,
    context_padding: int,
    max_hits_per_document: Optional[int],
):
    """Execute the search operation."""
    return search_operations.search_transcribed(
        keyword=keyword,
        max_results=max_results,
        show_context=browse,
        max_pages_with_context=max_pages if browse else 0,
        context_padding=context_padding if browse else 0,
        max_hits_per_document=max_hits_per_document,
    )


@app.command()
def search(
    keyword: Annotated[str, typer.Argument(help="Keyword to search for")],
    max_results: Annotated[
        int, typer.Option("--max", help="Maximum search results")
    ] = DEFAULT_MAX_RESULTS,
    max_display: Annotated[
        int, typer.Option(help="Maximum results to display")
    ] = DEFAULT_MAX_DISPLAY,
    browse: Annotated[
        bool, typer.Option("--browse", help="Show full page content for search hits (browse-style display)")
    ] = False,
    max_pages: Annotated[
        int, typer.Option(help="Maximum pages to load context for")
    ] = DEFAULT_MAX_PAGES,
    context_padding: Annotated[
        int,
        typer.Option(
            help="Number of pages to include before and after each hit for context (only with --browse)"
        ),
    ] = 0,
    max_hits_per_document: Annotated[
        Optional[int],
        typer.Option(
            "--max-hits-per-vol",
            help="Maximum number of hits to return per volume (useful for searching across many volumes)"
        ),
    ] = None,
    log: Annotated[
        bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")
    ] = False,
):
    """Search for keyword in transcribed materials.

    Fast search across all transcribed documents in Riksarkivet.
    Returns reference codes and page numbers containing the keyword.
    Use --browse to see full page transcriptions with optional context padding.

    When using --browse, the search automatically limits to 1 hit per volume to show
    more volumes instead of many hits within fewer volumes. Override with --max-hits-per-vol.

    Examples:
        ra search "Stockholm"                                    # Basic search
        ra search "trolldom" --browse --max-pages 5             # Browse many volumes (1 hit each)
        ra search "vasa" --browse --context-padding 2           # With surrounding pages
        ra search "Stockholm" --max-hits-per-vol 2              # Max 2 hits per volume
        ra search "Stockholm" --browse --max-hits-per-vol 3     # Browse with 3 hits per volume
        ra search "Stockholm" --max 100 --max-hits-per-vol 1    # Many volumes, 1 hit each
        ra search "Stockholm" --log                             # With API logging
    """
    http_client = get_http_client(log)
    search_operations = SearchOperations(http_client=http_client)
    display_service = CLIDisplayService(console)

    console.print(f"[blue]Searching for '{keyword}' in transcribed materials...[/blue]")
    show_logging_status(log)

    try:
        # When using --browse, default to 1 hit per volume to show more volumes
        # unless user explicitly specified a different value
        effective_max_hits_per_doc = max_hits_per_document
        if browse and max_hits_per_document is None:
            effective_max_hits_per_doc = 1
            console.print("[dim]Browse mode: limiting to 1 hit per volume to show more volumes[/dim]")

        search_result = perform_search(
            search_operations, keyword, max_results, browse, max_pages, context_padding, effective_max_hits_per_doc
        )

        display_search_summary(search_result, keyword)

        if browse and search_result.hits:
            display_context_results(search_result, display_service, keyword)
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
    browse_result, display_service, search_term: Optional[str], show_links: bool = False, show_success_message: bool = True
) -> None:
    """Display successful browse results grouped by reference code."""
    if show_success_message:
        console.print(
            f"[green]Successfully loaded {len(browse_result.contexts)} pages[/green]"
        )

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
        from rich.panel import Panel

        panel_content = []

        # Add document metadata at the top of the panel if available
        if browse_result.document_metadata:
            metadata = browse_result.document_metadata

            panel_content.append(f"[bold blue]📄 Volume:[/bold blue] {ref_code}")

            # Display title
            if metadata.title and metadata.title != "(No title)":
                panel_content.append(f"[blue]📋 Title:[/blue] {metadata.title}")

            # Display date range
            if metadata.date:
                panel_content.append(f"[blue]📅 Date:[/blue] {metadata.date}")

            # Display archival institution
            if metadata.archival_institution:
                institutions = metadata.archival_institution
                if institutions:
                    inst_names = [inst.get("caption", "") for inst in institutions]
                    panel_content.append(
                        f"[blue]🏛️  Institution:[/blue] {', '.join(inst_names)}"
                    )

            # Display hierarchy
            if metadata.hierarchy:
                hierarchy = metadata.hierarchy
                if hierarchy:
                    panel_content.append("[blue]📂 Archival Hierarchy:[/blue]")
                    for i, level in enumerate(hierarchy):
                        indent = "  " * (i + 1)
                        caption = level.get("caption", "")
                        # Replace newlines with spaces to keep hierarchy on single lines
                        caption = caption.replace("\n", " ").strip()
                        panel_content.append(f"{indent}• {caption}")

            # Display note if available
            if metadata.note:
                panel_content.append(f"[blue]📝 Note:[/blue] {metadata.note}")

            # Add spacing after metadata
            panel_content.append("")
        else:
            # If no metadata available, just show the document header
            panel_content.append(f"[bold blue]📄 Volume:[/bold blue] {ref_code}")
            panel_content.append("")

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

        # Create the grouped panel
        grouped_panel = Panel(
            "\n".join(panel_content),
            title=None,
            border_style="green",
            padding=(1, 1),
        )
        console.print("")  # Add spacing before the panel
        console.print(grouped_panel)


@app.command()
def browse(
    reference_code: Annotated[
        str, typer.Argument(help="Reference code of the document")
    ],
    pages: Annotated[
        Optional[str],
        typer.Option(help='Page range to display (e.g., "1-10" or "5,7,9")'),
    ] = None,
    page: Annotated[
        Optional[str],
        typer.Option(help="Single page or page range to display (alias for --pages)"),
    ] = None,
    search_term: Annotated[
        Optional[str], typer.Option(help="Highlight this term in the text")
    ] = None,
    max_display: Annotated[
        int, typer.Option(help="Maximum pages to display")
    ] = DEFAULT_MAX_DISPLAY,
    log: Annotated[
        bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")
    ] = False,
    show_links: Annotated[
        bool, typer.Option("--show-links", help="Display ALTO XML, Image, and Bildvisning links")
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
    display_service = CLIDisplayService(console)

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
    console.print(
        f"[blue]Starting MCP server with HTTP/SSE transport on {host}:{port}[/blue]"
    )
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
    log: Annotated[
        bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")
    ] = False,
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

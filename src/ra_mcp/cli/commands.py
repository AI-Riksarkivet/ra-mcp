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
from ..models import SearchOperation

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
    console.print(f"[blue]Searching for '{keyword}' in transcribed materials...[/blue]")
    console.print(
        f"[green]Found {len(search_result.hits)} page-level hits in {search_result.total_hits} documents[/green]"
    )


def display_context_results(search_result: SearchOperation, display_service: CLIDisplayService, no_grouping: bool) -> None:
    """Display search results with full context."""
    console.print(
        f"[green]Successfully loaded context for {len(search_result.hits)} pages[/green]"
    )

    formatted_results = display_service.format_show_pages_results(
        search_result, search_result.hits, no_grouping
    )

    if isinstance(formatted_results, list):
        console.print(
            f"\n[bold]Search Results {'with Full Page Context' if no_grouping else 'Grouped by Document'} ({len(search_result.hits)} pages):[/bold]"
        )
        for panel in formatted_results:
            console.print(panel)
    else:
        console.print(formatted_results)


def display_table_results(search_result: SearchOperation, display_service: CLIDisplayService, max_display: int, keyword: str) -> None:
    """Display search results in table format."""
    formatted_table = display_service.format_search_results(
        search_result, max_display, False
    )

    if not formatted_table:
        return

    summary = display_service.get_search_summary(search_result)
    summary_lines = display_service.formatter.format_search_summary(summary)
    for line in summary_lines:
        console.print(line)

    if isinstance(formatted_table, str):
        console.print(formatted_table)
    else:
        console.print(formatted_table)
        display_browse_examples(summary, display_service, keyword)
        display_remaining_documents(summary, display_service, max_display)


def display_browse_examples(summary: dict, display_service: CLIDisplayService, keyword: str) -> None:
    """Display example browse commands."""
    grouped_hits = summary.get("grouped_hits", {})
    example_lines = display_service.formatter.format_browse_example(
        grouped_hits, keyword
    )
    for line in example_lines:
        console.print(line)


def display_remaining_documents(summary: dict, display_service: CLIDisplayService, max_display: int) -> None:
    """Display message about remaining documents."""
    grouped_hits = summary.get("grouped_hits", {})
    total_groups = len(grouped_hits)
    remaining_message = display_service.formatter.format_remaining_documents(
        total_groups, max_display
    )
    if remaining_message:
        console.print(remaining_message)


def perform_search(search_operations, keyword: str, max_results: int,
                  context: bool, max_pages: int, context_padding: int):
    """Execute the search operation."""
    return search_operations.search_transcribed(
        keyword=keyword,
        max_results=max_results,
        show_context=context,
        max_pages_with_context=max_pages if context else 0,
        context_padding=context_padding if context else 0,
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
    context: Annotated[
        bool, typer.Option(help="Show full page context for search hits")
    ] = False,
    max_pages: Annotated[
        int, typer.Option(help="Maximum pages to load context for")
    ] = DEFAULT_MAX_PAGES,
    no_grouping: Annotated[
        bool,
        typer.Option(
            help="Show pages individually instead of grouped by document (only with --context)"
        ),
    ] = False,
    context_padding: Annotated[
        int,
        typer.Option(
            help="Number of pages to include before and after each hit for context (only with --context)"
        ),
    ] = 0,
    log: Annotated[
        bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")
    ] = False,
):
    """Search for keyword in transcribed materials.

    Fast search across all transcribed documents in Riksarkivet.
    Returns reference codes and page numbers containing the keyword.
    Use --context to see full page transcriptions with optional context padding.

    Examples:
        ra search "Stockholm"                                    # Basic search
        ra search "trolldom" --context --max-pages 5            # With full context
        ra search "vasa" --context --context-padding 2          # With surrounding pages
        ra search "Stockholm" --context --no-grouping           # Individual page display
        ra search "Stockholm" --log                             # With API logging
    """
    http_client = get_http_client(log)
    search_operations = SearchOperations(http_client=http_client)
    display_service = CLIDisplayService(console)

    console.print(f"[blue]Searching for '{keyword}' in transcribed materials...[/blue]")
    show_logging_status(log)

    try:
        search_result = perform_search(
            search_operations, keyword, max_results,
            context, max_pages, context_padding
        )

        display_search_summary(search_result, keyword)

        if context and search_result.hits:
            display_context_results(search_result, display_service, no_grouping)
        else:
            display_table_results(search_result, display_service, max_display, keyword)

    except Exception as error:
        console.print(f"[red]Search failed: {error}[/red]")
        raise typer.Exit(code=1)


def display_browse_header(reference_code: str) -> None:
    """Display browse operation header."""
    console.print(f"[blue]Looking up reference code: {reference_code}[/blue]")


def load_document_with_progress(search_operations, reference_code: str,
                               pages: str, search_term: str, max_display: int):
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


def display_browse_results(browse_result, display_service, search_term: str) -> None:
    """Display successful browse results."""
    console.print(
        f"[green]Successfully loaded {len(browse_result.contexts)} pages[/green]"
    )
    console.print(
        f"\n[bold]Full Page Transcriptions ({len(browse_result.contexts)} pages):[/bold]"
    )

    formatted_pages = display_service.format_browse_results(browse_result, search_term)

    if isinstance(formatted_pages, list):
        for panel in formatted_pages:
            console.print(panel)
    else:
        console.print(formatted_pages)


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
            max_display
        )

        if not browse_result.contexts:
            display_browse_error(reference_code)
            raise typer.Exit(code=1)

        display_browse_results(browse_result, display_service, search_term)

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
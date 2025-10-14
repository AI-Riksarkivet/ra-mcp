"""
CLI commands for Riksarkivet MCP server.
"""

from typing import Optional, Annotated
import os

import typer
from rich.console import Console

from ..services import SearchOperations
from ..services.display_service import DisplayService
from ..formatters import RichConsoleFormatter
from ..utils.http_client import get_http_client
from ..config import DEFAULT_MAX_RESULTS, DEFAULT_MAX_DISPLAY
from .cli_progress import perform_search_with_progress, load_document_with_progress

console = Console()
app = typer.Typer()


@app.command()
def search(
    keyword: Annotated[str, typer.Argument(help="Keyword to search for")],
    max_results: Annotated[int, typer.Option("--max", help="Maximum search results")] = DEFAULT_MAX_RESULTS,
    max_display: Annotated[int, typer.Option(help="Maximum results to display")] = DEFAULT_MAX_DISPLAY,
    max_hits_per_document: Annotated[
        Optional[int],
        typer.Option(
            "--max-hits-per-vol",
            help="Maximum number of hits to return per volume (useful for searching across many volumes)",
        ),
    ] = 3,
    log: Annotated[bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")] = False,
):
    """Search for keyword in transcribed materials.

    Fast search across all transcribed documents in Riksarkivet.
    Returns reference codes and page numbers containing the keyword.

    By default, returns up to 3 hits per volume. Use --max-hits-per-vol to adjust.

    Examples:
        ra search "Stockholm"                                    # Basic search (3 hits per volume)
        ra search "Stockholm" --max-hits-per-vol 2              # Max 2 hits per volume
        ra search "Stockholm" --max 100 --max-hits-per-vol 1    # Many volumes, 1 hit each
        ra search "Stockholm" --log                             # With API logging
    """
    http_client = get_http_client(log)
    search_operations = SearchOperations(http_client=http_client)
    display_service = DisplayService(formatter=RichConsoleFormatter(console))

    # Show logging status if enabled
    status_msg = display_service.format_logging_status(log)
    if status_msg:
        console.print(status_msg)

    try:
        # Use the specified max_hits_per_document value (defaults to 3)
        effective_max_hits_per_doc = max_hits_per_document

        search_result = perform_search_with_progress(
            search_operations,
            keyword,
            max_results,
            effective_max_hits_per_doc,
            console,
        )

        # Use DisplayService to format and display search results
        formatted_output = display_service.format_search_results_with_summary(
            search_result, max_display, keyword
        )
        for item in formatted_output:
            console.print(item)

    except Exception as error:
        console.print(f"[red]Search failed: {error}[/red]")
        raise typer.Exit(code=1)


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

    # Display browse header
    console.print(display_service.format_browse_header(reference_code))

    # Show logging status if enabled
    status_msg = display_service.format_logging_status(log)
    if status_msg:
        console.print(status_msg)

    requested_pages = page if page is not None else pages

    try:
        browse_result = load_document_with_progress(
            search_operations,
            reference_code,
            requested_pages or "1-20",
            search_term,
            max_display,
            console,
        )

        if not browse_result.contexts:
            # Use DisplayService to format error message
            error_lines = display_service.format_browse_error(reference_code)
            for line in error_lines:
                console.print(line)
            raise typer.Exit(code=1)

        # Use DisplayService to format and display results
        formatted_output = display_service.format_browse_results(
            browse_result,
            highlight_term=search_term,
            show_links=show_links,
            show_success_message=True,
        )

        # Print each item in the output (messages and panels)
        for item in formatted_output:
            console.print(item)

    except Exception as error:
        console.print(f"[red]Browse failed: {error}[/red]")
        raise typer.Exit(code=1)


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
    import sys
    from ..server import main as server_main

    if log:
        os.environ["RA_MCP_LOG_API"] = "1"
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")

    # Prepare arguments for server
    original_argv = sys.argv
    if port:
        console.print(f"[blue]Starting MCP server with HTTP/SSE transport on {host}:{port}[/blue]")
        sys.argv = ["ra-mcp-server", "--http", "--port", str(port), "--host", host]
    else:
        console.print("[blue]Starting MCP server with stdio transport[/blue]")
        sys.argv = ["ra-mcp-server"]

    try:
        server_main()
    finally:
        sys.argv = original_argv


@app.callback()
def main_callback():
    """
    Riksarkivet MCP Server and CLI Tools.

    Search and browse transcribed historical documents from the Swedish National Archives.
    """
    pass

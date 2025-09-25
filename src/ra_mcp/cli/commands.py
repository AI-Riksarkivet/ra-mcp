"""
Refactored CLI commands using the shared business logic layer.
This eliminates code duplication with the MCP tools.
"""

from typing import Optional, Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..services import SearchOperations
from ..services.cli_display_service import CLIDisplayService
from ..config import DEFAULT_MAX_RESULTS, DEFAULT_MAX_DISPLAY, DEFAULT_MAX_PAGES

console = Console()
app = typer.Typer()


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
    """
    # Initialize services
    search_ops = SearchOperations()
    display_service = CLIDisplayService(console)

    console.print(f"[blue]Searching for '{keyword}' in transcribed materials...[/blue]")

    try:
        # Perform search using shared logic
        operation = search_ops.search_transcribed(
            keyword=keyword,
            max_results=max_results,
            show_context=context,
            max_pages_with_context=max_pages if context else 0,
            context_padding=context_padding if context else 0,
        )

        console.print(
            f"[green]Found {len(operation.hits)} page-level hits in {operation.total_hits} documents[/green]"
        )

        if context and operation.hits:
            # Show context with full page transcriptions
            console.print(
                f"[green]Successfully loaded context for {len(operation.hits)} pages[/green]"
            )

            # Use display service for formatted output
            result = display_service.format_show_pages_results(
                operation, operation.hits, no_grouping
            )

            # Handle Rich objects (panels)
            if isinstance(result, list):
                console.print(
                    f"\n[bold]Search Results {'with Full Page Context' if no_grouping else 'Grouped by Document'} ({len(operation.hits)} pages):[/bold]"
                )
                for panel in result:
                    console.print(panel)
            else:
                # String output (shouldn't happen with RichConsoleFormatter)
                console.print(result)

        else:
            # Use display service for table display
            result = display_service.format_search_results(
                operation, max_display, False
            )

            if result:
                # Get and display summary
                summary = display_service.get_search_summary(operation)
                summary_lines = display_service.formatter.format_search_summary(summary)
                for line in summary_lines:
                    console.print(line)

                # Display the table or message
                if isinstance(result, str):
                    console.print(result)
                else:
                    # Rich Table object
                    console.print(result)

                    # Show example browse command
                    grouped_hits = summary.get("grouped_hits", {})
                    example_lines = display_service.formatter.format_browse_example(
                        grouped_hits, keyword
                    )
                    for line in example_lines:
                        console.print(line)

                    # Show remaining documents message
                    total_groups = len(grouped_hits)
                    remaining_msg = (
                        display_service.formatter.format_remaining_documents(
                            total_groups, max_display
                        )
                    )
                    if remaining_msg:
                        console.print(remaining_msg)

    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        raise typer.Exit(code=1)


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
):
    """Browse pages by reference code.

    You can specify pages using either --pages or --page (they work the same way).
    If both are provided, --page takes precedence.

    Examples:
        ra browse "SE/RA/123" --page 5
        ra browse "SE/RA/123" --pages "1-10"
        ra browse "SE/RA/123" --page "5,7,9"
    """
    # Initialize services
    search_ops = SearchOperations()
    display_service = CLIDisplayService(console)

    console.print(f"[blue]Looking up reference code: {reference_code}[/blue]")

    # Handle both --pages and --page options
    page_range = page if page is not None else pages

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading document information...", total=None)

            # Perform browse using shared logic
            operation = search_ops.browse_document(
                reference_code=reference_code,
                pages=page_range or "1-20",
                highlight_term=search_term,
                max_pages=max_display,
            )

            progress.update(task, description=f"✓ Found PID: {operation.pid}")

        if not operation.contexts:
            console.print(f"[red]Could not load pages for {reference_code}[/red]")
            console.print("[yellow]Suggestions:[/yellow]")
            console.print("• Check the reference code format")
            console.print("• Try different page numbers")
            console.print("• The document might not have transcriptions")
            raise typer.Exit(code=1)

        console.print(
            f"[green]Successfully loaded {len(operation.contexts)} pages[/green]"
        )

        # Use display service for formatted output
        console.print(
            f"\n[bold]Full Page Transcriptions ({len(operation.contexts)} pages):[/bold]"
        )

        result = display_service.format_browse_results(operation, search_term)

        # Handle Rich panels
        if isinstance(result, list):
            for panel in result:
                console.print(panel)
        else:
            # String output (shouldn't happen with RichConsoleFormatter)
            console.print(result)

    except Exception as e:
        console.print(f"[red]Browse failed: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def serve(
    port: Annotated[
        Optional[int],
        typer.Option(help="Port for HTTP/SSE transport (enables HTTP mode)"),
    ] = None,
    host: Annotated[str, typer.Option(help="Host for HTTP transport")] = "localhost",
):
    """Start the MCP server.

    Examples:
        ra serve                    # Start with stdio transport
        ra serve --port 8000        # Start with HTTP/SSE transport on port 8000
    """
    if port:
        console.print(
            f"[blue]Starting MCP server with HTTP/SSE transport on {host}:{port}[/blue]"
        )
        # Import and run the HTTP server
        from ..server import main as server_main
        import sys

        # Set up sys.argv for the server
        original_argv = sys.argv
        sys.argv = ["ra-mcp-server", "--http", "--port", str(port), "--host", host]

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
        sys.argv = ["ra-mcp-server"]

        try:
            server_main()
        finally:
            sys.argv = original_argv


# Create a callback for the app to handle errors gracefully
@app.callback()
def main_callback():
    """
    Riksarkivet MCP Server and CLI Tools.

    Search and browse transcribed historical documents from the Swedish National Archives.
    """
    pass

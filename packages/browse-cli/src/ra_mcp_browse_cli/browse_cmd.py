"""
Browse command for CLI.
"""

from typing import Optional, Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ra_mcp_common.utils.http_client import get_http_client
from ra_mcp_browse.operations import BrowseOperations
from ra_mcp_browse.config import DEFAULT_MAX_PAGES

from .formatting import RichConsoleFormatter

DEFAULT_MAX_DISPLAY = 20  # CLI display limit

console = Console()


def browse(
    reference_code: Annotated[
        str, typer.Argument(help="Document reference code from search results (e.g., 'SE/RA/420422/01')")
    ],
    pages: Annotated[
        Optional[str],
        typer.Option(help='Page specification: single ("5"), range ("1-10"), or list ("5,7,9"). Alias: --page'),
    ] = None,
    page: Annotated[
        Optional[str],
        typer.Option(help='Page specification: single ("5"), range ("1-10"), or list ("5,7,9"). Shorthand for --pages'),
    ] = None,
    search_term: Annotated[
        Optional[str], typer.Option("--search-term", help="Highlight keyword in transcribed text (case-insensitive)")
    ] = None,
    max_display: Annotated[
        int, typer.Option("--max-display", help="Maximum number of pages to display in output")
    ] = DEFAULT_MAX_DISPLAY,
    log: Annotated[
        bool, typer.Option("--log", help="Enable detailed API request/response logging to ra_mcp_api.log file")
    ] = False,
    show_links: Annotated[
        bool,
        typer.Option("--show-links", help="Display direct links to ALTO XML, IIIF images, and Bildvisaren viewer"),
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
    browse_operations = BrowseOperations(http_client=http_client)
    formatter = RichConsoleFormatter(console)

    # Display browse header
    console.print(f"\n[bold cyan]📖 Browsing document: {reference_code}[/bold cyan]\n")

    # Show logging status if enabled
    if log:
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")

    requested_pages = page if page is not None else pages

    try:
        # Load document with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            loading_task = progress.add_task("Loading document information...", total=None)

            browse_result = browse_operations.browse_document(
                reference_code=reference_code,
                pages=requested_pages or "1-20",
                highlight_term=search_term,
                max_pages=max_display,
            )

            progress.update(
                loading_task,
                description=f"✓ Found manifest_id: {browse_result.manifest_id}",
            )

        if not browse_result.contexts:
            # Format error message
            console.print(f"[yellow]No pages found for '{reference_code}'[/yellow]")
            console.print("\n[dim]Suggestions:[/dim]")
            console.print("[dim]- Check the reference code format[/dim]")
            console.print("[dim]- Verify the document has transcribed pages[/dim]")
            console.print("[dim]- Try different page numbers[/dim]")
            raise typer.Exit(code=1)

        # Format and display results directly
        formatted_output = formatter.format_browse_results(
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

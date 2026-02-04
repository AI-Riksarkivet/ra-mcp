"""
Browse command for CLI.
"""

from typing import Optional, Annotated

import typer
from rich.console import Console

from ra_mcp_core.config import DEFAULT_MAX_DISPLAY
from ra_mcp_core.formatters import RichConsoleFormatter
from ra_mcp_core.utils.http_client import get_http_client

from ..services import BrowseOperations
from ..services.browse_display_service import BrowseDisplayService
from .cli_progress import load_document_with_progress

console = Console()


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
    browse_operations = BrowseOperations(http_client=http_client)
    browse_display_service = BrowseDisplayService(formatter=RichConsoleFormatter(console))

    # Display browse header
    console.print(browse_display_service.format_browse_header(reference_code))

    # Show logging status if enabled
    if log:
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")

    requested_pages = page if page is not None else pages

    try:
        browse_result = load_document_with_progress(
            browse_operations,
            reference_code,
            requested_pages or "1-20",
            search_term,
            max_display,
            console,
        )

        if not browse_result.contexts:
            # Use DisplayService to format error message
            error_lines = browse_display_service.format_browse_error(reference_code)
            for line in error_lines:
                console.print(line)
            raise typer.Exit(code=1)

        # Use DisplayService to format and display results
        formatted_output = browse_display_service.format_browse_results(
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

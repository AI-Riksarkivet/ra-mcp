"""
Search command for CLI.
"""

from typing import Optional, Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ra_mcp_core.config import DEFAULT_MAX_RESULTS, DEFAULT_MAX_DISPLAY
from ra_mcp_core.formatters import RichConsoleFormatter
from ra_mcp_core.utils.http_client import get_http_client

from ..services import SearchOperations
from ..services.search_display_service import SearchDisplayService

console = Console()


def search(
    keyword: Annotated[str, typer.Argument(help="Keyword to search for")],
    max_results: Annotated[int, typer.Option("--max", help="Maximum search results")] = DEFAULT_MAX_RESULTS,
    max_display: Annotated[int, typer.Option(help="Maximum results to display")] = DEFAULT_MAX_DISPLAY,
    max_snippets_per_record: Annotated[
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
    search_display_service = SearchDisplayService(formatter=RichConsoleFormatter(console))

    # Show logging status if enabled
    if log:
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")

    try:
        # Use the specified max_snippets_per_record value (defaults to 3)
        effective_max_hits_per_doc = max_snippets_per_record

        # Execute search with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            search_task = progress.add_task(f"Searching for '{keyword}' across all transcribed volumes...", total=None)

            search_result = search_operations.search_transcribed(
                keyword=keyword,
                max_results=max_results,
                max_snippets_per_record=effective_max_hits_per_doc,
            )

            # Update with detailed results
            snippet_count = search_result.count_snippets()
            progress.update(
                search_task,
                description=f"✓ Found {snippet_count} page hits across {len(search_result.items)} volumes",
            )

        # Use DisplayService to format and display search results
        formatted_output = search_display_service.format_search_results_with_summary(search_result, max_display, keyword)
        for item in formatted_output:
            console.print(item)

    except Exception as error:
        console.print(f"[red]Search failed: {error}[/red]")
        raise typer.Exit(code=1)

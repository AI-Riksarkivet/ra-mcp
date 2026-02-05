"""
Search command for CLI.
"""

from typing import Optional, Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ra_mcp_common.utils.http_client import get_http_client
from ra_mcp_search.config import DEFAULT_MAX_RESULTS, DEFAULT_MAX_DISPLAY
from ra_mcp_search.operations import SearchOperations

from .formatting import RichConsoleFormatter

console = Console()


def search(
    keyword: Annotated[
        str,
        typer.Argument(
            help="Search term or Solr query. Supports wildcards (*), fuzzy (~), Boolean (AND/OR/NOT), proximity (~N), and more"
        ),
    ],
    max_results: Annotated[
        int, typer.Option("--max", help="Maximum number of records to fetch from API (pagination size)")
    ] = DEFAULT_MAX_RESULTS,
    max_display: Annotated[
        int, typer.Option("--max-display", help="Maximum number of records to display in output")
    ] = DEFAULT_MAX_DISPLAY,
    max_snippets_per_record: Annotated[
        Optional[int],
        typer.Option(
            "--max-hits-per-vol",
            help="Limit hits per volume (useful for broad searches across many volumes). Default: 3 hits per volume",
        ),
    ] = 3,
    transcribed_only: Annotated[
        bool,
        typer.Option("--transcribed-only/--all-fields", help="Search only transcribed text (default) or all fields including metadata")
    ] = True,
    only_digitised: Annotated[
        bool,
        typer.Option("--digitised-only/--all-materials", help="Limit to digitised materials with images (default) or search all records")
    ] = True,
    log: Annotated[
        bool, typer.Option("--log", help="Enable detailed API request/response logging to ra_mcp_api.log file")
    ] = False,
):
    """Search for keyword in historical documents.

    Fast search across Riksarkivet collections. By default searches transcribed text in digitised materials.
    Use --all-fields to search metadata (titles, names, places, etc.).

    NOTE: Transcribed text search only works with digitised materials. If you use --all-materials,
    the search automatically switches to metadata search (--all-fields is implied).

    By default, returns up to 3 hits per volume. Use --max-hits-per-vol to adjust.

    Examples:
        ra search "Stockholm"                                    # Basic transcribed text search (3 hits per volume)
        ra search "Stockholm" --all-fields                      # Search all fields including metadata
        ra search "Stockholm" --all-fields --all-materials      # Search all fields in all materials
        ra search "Stockholm" --max-hits-per-vol 2              # Max 2 hits per volume
        ra search "Stockholm" --max 100 --max-hits-per-vol 1    # Many volumes, 1 hit each
        ra search "Stockholm" --log                             # With API logging
    """
    http_client = get_http_client(log)
    search_operations = SearchOperations(http_client=http_client)
    formatter = RichConsoleFormatter(console)

    # Show logging status if enabled
    if log:
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")

    try:
        # Transcribed text search requires digitised materials
        # If user wants all materials, automatically use metadata search
        if not only_digitised and transcribed_only:
            console.print("[yellow]⚠️  Note: Transcribed text search requires digitised materials.[/yellow]")
            console.print("[yellow]   Switching to metadata search (--all-fields) for all materials.[/yellow]\n")
            transcribed_only = False

        # Use the specified max_snippets_per_record value (defaults to 3)
        effective_max_hits_per_doc = max_snippets_per_record

        # Execute search with progress indicator
        search_type = "transcribed text" if transcribed_only else "all fields"
        material_filter = "digitised materials" if only_digitised else "all materials"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            search_task = progress.add_task(
                f"Searching {search_type} in {material_filter} for '{keyword}'...",
                total=None
            )

            search_result = search_operations.search(
                keyword=keyword,
                transcribed_only=transcribed_only,
                only_digitised=only_digitised,
                max_results=max_results,
                max_snippets_per_record=effective_max_hits_per_doc,
            )

            # Update with detailed results
            snippet_count = search_result.count_snippets()
            progress.update(
                search_task,
                description=f"✓ Found {snippet_count} page hits across {len(search_result.items)} volumes",
            )

        # Format and display search results directly
        table = formatter.format_search_results(search_result, max_display)
        console.print(table)

        # Display summary statistics
        snippet_count = search_result.count_snippets()
        records_count = len(search_result.items)
        summary_lines = formatter.format_search_summary_stats(
            snippet_count=snippet_count,
            records_count=records_count,
            total_hits=search_result.response.total_hits,
            offset=search_result.offset,
        )
        for line in summary_lines:
            console.print(line)

        # Display example browse command
        example_lines = formatter.format_browse_example(search_result.items, keyword)
        for line in example_lines:
            console.print(line)

        # Display remaining documents message
        remaining_msg = formatter.format_remaining_documents(len(search_result.items), max_display)
        if remaining_msg:
            console.print(remaining_msg)

    except Exception as error:
        console.print(f"[red]Search failed: {error}[/red]")
        raise typer.Exit(code=1)

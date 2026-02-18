"""
Search command for CLI.
"""

from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ra_mcp_common.telemetry import get_tracer
from ra_mcp_common.utils.http_client import get_http_client
from ra_mcp_search.config import DEFAULT_MAX_DISPLAY, DEFAULT_MAX_RESULTS
from ra_mcp_search.search_operations import SearchOperations

from .formatting import RichConsoleFormatter


_tracer = get_tracer("ra_mcp.cli.search")

console = Console()


def _print_renderables(renderables, console: Console) -> None:
    for item in renderables:
        console.print(item)


def search(
    keyword: Annotated[
        str,
        typer.Argument(help="Search term or Solr query. Supports wildcards (*), fuzzy (~), Boolean (AND/OR/NOT), proximity (~N), and more"),
    ],
    max_results: Annotated[int, typer.Option("--max", help="Maximum number of records to fetch from API (pagination size)")] = DEFAULT_MAX_RESULTS,
    max_display: Annotated[int, typer.Option("--max-display", help="Maximum number of records to display in output")] = DEFAULT_MAX_DISPLAY,
    max_snippets_per_record: Annotated[
        int | None,
        typer.Option(
            "--max-hits-per-vol",
            help="Limit hits per volume (useful for broad searches across many volumes). Default: 3 hits per volume",
        ),
    ] = 3,
    transcribed_only: Annotated[
        bool, typer.Option("--transcribed-text/--text", help="Search transcribed text (default) or general text fields (metadata)")
    ] = True,
    only_digitised: Annotated[
        bool, typer.Option("--only-digitised-materials/--include-all-materials", help="Limit to digitised materials (default) or include all records")
    ] = True,
    log: Annotated[bool, typer.Option("--log", help="Enable detailed API request/response logging to ra_mcp_api.log file")] = False,
) -> None:
    """Search for keyword in historical documents.

    Fast search across Riksarkivet collections. Flags match the API parameters exactly.

    API Parameters (mapped to flags):
    - transcribed_text: AI-transcribed text search (requires only_digitised_materials=true)
    - text: General metadata search (titles, names, places, provenance)
    - only_digitised_materials: Filter for digitised materials with images

    NOTE: --transcribed-text requires --only-digitised-materials (can't search transcriptions
    of non-digitised materials). Using --include-all-materials automatically switches to --text.

    By default, returns up to 3 hits per volume. Use --max-hits-per-vol to adjust.

    Examples:
        ra search "Stockholm"                                        # transcribed_text + only_digitised_materials
        ra search "Stockholm" --text                                # text + only_digitised_materials
        ra search "Stockholm" --include-all-materials               # text + all materials (auto-switches)
        ra search "Stockholm" --max-hits-per-vol 2                  # Limit hits per volume
        ra search "Stockholm" --max 100 --max-hits-per-vol 1        # Many volumes, 1 hit each
        ra search "Stockholm" --log                                 # With API logging
    """
    http_client = get_http_client(log)
    search_operations = SearchOperations(http_client=http_client)
    formatter = RichConsoleFormatter(console)

    if log:
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")

    with _tracer.start_as_current_span("cli.search", attributes={"search.keyword": keyword}):
        try:
            if not only_digitised and transcribed_only:
                console.print("[yellow]Note: --transcribed-text requires --only-digitised-materials[/yellow]")
                console.print("[yellow]   Automatically switching to --text when --include-all-materials is used.[/yellow]\n")
                transcribed_only = False

            search_type = "transcribed text" if transcribed_only else "all fields"
            material_filter = "digitised materials" if only_digitised else "all materials"

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(
                    f"Searching {search_type} in {material_filter} for '{keyword}'...",
                    total=None,
                )

                search_result = search_operations.search(
                    keyword=keyword,
                    transcribed_only=transcribed_only,
                    only_digitised=only_digitised,
                    max_results=max_results,
                    max_snippets_per_record=max_snippets_per_record,
                )

            snippet_count = search_result.count_snippets()
            records_count = len(search_result.items)

            console.print(formatter.format_search_results(search_result, max_display))

            _print_renderables(
                formatter.format_search_summary_stats(
                    snippet_count=snippet_count,
                    records_count=records_count,
                    total_hits=search_result.response.total_hits,
                    offset=search_result.offset,
                    max_requested=search_result.max,
                ),
                console,
            )

            _print_renderables(
                formatter.format_browse_example(search_result.items, keyword),
                console,
            )

            remaining_msg = formatter.format_remaining_documents(records_count, max_display)
            if remaining_msg:
                console.print(remaining_msg)

        except typer.Exit:
            raise
        except Exception as error:
            console.print(f"[red]Search failed: {error}[/red]")
            raise typer.Exit(code=1) from error

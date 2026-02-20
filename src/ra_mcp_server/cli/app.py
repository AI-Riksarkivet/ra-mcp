"""
Main CLI entry point for ra-mcp.
"""

import os
from typing import Annotated

import typer
from rich.console import Console

from ra_mcp_browse_cli import browse_app
from ra_mcp_search_cli import search_app
from ra_mcp_tui import tui_app


console = Console()

app = typer.Typer(
    name="ra",
    help="""Riksarkivet MCP - Swedish National Archives Tools.

Access transcribed historical documents from the Swedish National Archives (Riksarkivet).

Available Commands:
  search     - Search transcribed documents with advanced query syntax
  browse     - View full page transcriptions by reference code
  tui        - Interactive terminal browser for documents
  serve      - Start the MCP server (composable, modular architecture)

Quick Start:
  ra search "Stockholm"              # Search for a keyword
  ra browse "SE/RA/123" --page 5     # View a specific page
  ra tui "trolldom"                  # Launch interactive TUI
  ra serve --port 8000               # Start MCP server
  ra serve --list-modules            # List available server modules

For detailed help on any command:
  ra search --help
  ra browse --help
  ra tui --help
  ra serve --help
    """,
    rich_markup_mode="markdown",
    no_args_is_help=True,
)

# Import commands from search_app and browse_app and add them to the root app
# This merges the search and browse commands at the root level
for command in search_app.registered_commands:
    app.registered_commands.append(command)

for command in browse_app.registered_commands:
    app.registered_commands.append(command)

for command in tui_app.registered_commands:
    app.registered_commands.append(command)


@app.command()
def serve(
    port: Annotated[
        int | None,
        typer.Option(help="Port for HTTP/SSE transport (enables HTTP mode)"),
    ] = None,
    host: Annotated[str, typer.Option(help="Host for HTTP transport")] = "localhost",
    log: Annotated[bool, typer.Option("--log", help="Enable API call logging to ra_mcp_api.log")] = False,
    modules: Annotated[
        str | None,
        typer.Option(help="Comma-separated list of modules to enable (e.g., search,browse,guide)"),
    ] = None,
    list_modules: Annotated[
        bool,
        typer.Option("--list-modules", help="List available modules and exit"),
    ] = False,
    verbose: Annotated[bool, typer.Option("-v", "--verbose", help="Enable verbose logging")] = False,
) -> None:
    """Start the MCP server.

    The server is composable - you can enable/disable modules as needed.

    Examples:
        ra serve                              # Start with all default modules (stdio)
        ra serve --port 8000                  # Start HTTP server with all modules
        ra serve --modules search,browse      # Start with only search and browse
        ra serve --list-modules               # List available modules
        ra serve --port 8000 --log            # HTTP server with API logging
    """
    from ..server import AVAILABLE_MODULES, run_server

    # Handle --list-modules
    if list_modules:
        console.print("\n[bold]Available modules:[/bold]\n")
        for name, info in AVAILABLE_MODULES.items():
            default_marker = "[dim](default)[/dim]" if info["default"] else ""
            console.print(f"  [cyan]{name:12}[/cyan] - {info['description']} {default_marker}")
        console.print()
        return

    if log:
        os.environ["RA_MCP_LOG_API"] = "1"
        console.print("[dim]API logging enabled - check ra_mcp_api.log[/dim]")

    if port:
        console.print(f"[blue]Starting MCP server with HTTP/SSE transport on {host}:{port}[/blue]")
    else:
        console.print("[blue]Starting MCP server with stdio transport[/blue]")

    if modules:
        console.print(f"[dim]Enabled modules: {modules}[/dim]")

    run_server(http=port is not None, port=port or 8000, host=host, verbose=verbose, modules=modules)


@app.callback()
def main_callback() -> None:
    """
    Riksarkivet MCP Server and CLI Tools.

    Search and browse transcribed historical documents from the Swedish National Archives.
    """
    import atexit

    from ra_mcp_server.telemetry import init_telemetry, shutdown_telemetry

    init_telemetry()
    atexit.register(shutdown_telemetry)


if __name__ == "__main__":
    app()

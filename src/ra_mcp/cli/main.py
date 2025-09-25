"""
Main CLI entry point for ra-mcp.
"""

import typer

from .commands import search, browse, serve

app = typer.Typer(
    name="ra",
    help="""Riksarkivet MCP Server and CLI Tools.

Search and browse transcribed historical documents from the Swedish National Archives.

Commands:
  search     - Search for keywords in transcribed materials
  browse     - Browse pages by reference code
  serve      - Start the MCP server

Examples:
  ra search "Stockholm"                          # Search for keyword
  ra search "trolldom" --context --max-pages 5  # Search with full context
  ra browse "SE/RA/123" --page 5                 # Browse specific page
  ra serve                                       # Start MCP server
    """,
    rich_markup_mode="markdown",
    no_args_is_help=True,
)

app.command()(search)
app.command()(browse)
app.command()(serve)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

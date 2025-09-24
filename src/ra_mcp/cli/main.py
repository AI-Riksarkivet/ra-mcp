"""
Main CLI entry point for ra-mcp.
"""

import click

from .commands import search, browse, serve


@click.group()
def main():
    """Riksarkivet MCP Server and CLI Tools.

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
    """
    pass


# Add commands to the main group
main.add_command(search)
main.add_command(browse)
main.add_command(serve)


if __name__ == "__main__":
    main()

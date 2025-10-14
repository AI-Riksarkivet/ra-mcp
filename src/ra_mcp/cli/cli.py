"""
Main CLI entry point for ra-mcp.
"""

import typer

from ra_mcp.cli.commands import search, browse, serve

app = typer.Typer(
    name="ra",
    help="""Riksarkivet MCP Server and CLI Tools.

Search and browse transcribed historical documents from the Swedish National Archives.

Commands:
  search     - Search for keywords in transcribed materials
  browse     - Browse pages by reference code
  serve      - Start the MCP server

Search Syntax:
  Exact:      "Stockholm"                    - Find exact matches
  Wildcard:   "St?ckholm", "Stock*", "*holm" - ? = single char, * = multiple chars
  Fuzzy:      "Stockholm~", "Stockholm~1"    - Find similar terms (edit distance)
  Proximity:  "Stockholm trolldom"~10        - Words within N words of each other
  Boosting:   "Stockholm^4 trol*"            - Increase term relevance
  Boolean:    (Stockholm AND trolldom)       - AND, OR, NOT operators
  Required:   +Stockholm -trolldom           - Require (+) or exclude (-) terms
  Grouping:   ((Stockholm OR Göteborg) AND troll*)  - Complex sub-queries

Examples:
  ra search "Stockholm"                          # Basic search
  ra search "St*holm"                            # Wildcard search
  ra search "Stockholm~"                         # Fuzzy search
  ra search "(Stockholm AND trolldom)"           # Boolean search
  ra browse "SE/RA/123" --page 5                 # Browse specific page
  ra serve                                       # Start MCP server
    """,
    rich_markup_mode="markdown",
    no_args_is_help=True,
)

app.command()(search)
app.command()(browse)
app.command()(serve)


if __name__ == "__main__":
    app()

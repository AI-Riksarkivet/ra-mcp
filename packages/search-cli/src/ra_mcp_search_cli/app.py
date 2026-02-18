"""
CLI sub-application for search command.
"""

import typer

from .search_cmd import search


search_app = typer.Typer(
    name="search",
    help="Search transcribed historical documents from the Swedish National Archives.",
    no_args_is_help=True,
)

# Register command
search_app.command()(search)

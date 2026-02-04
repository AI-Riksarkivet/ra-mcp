"""
CLI sub-application for search and browse commands.
"""

import typer

from .search_cmd import search
from .browse_cmd import browse

search_app = typer.Typer(
    name="search-browse",
    help="Search and browse transcribed historical documents from the Swedish National Archives.",
    no_args_is_help=True,
)

# Register commands
search_app.command()(search)
search_app.command()(browse)

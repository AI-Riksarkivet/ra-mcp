"""
CLI sub-application for browse command.
"""

import typer

from .browse_cmd import browse


browse_app = typer.Typer(
    name="browse",
    help="Browse document pages from the Swedish National Archives.",
    no_args_is_help=True,
)

# Register command
browse_app.command()(browse)

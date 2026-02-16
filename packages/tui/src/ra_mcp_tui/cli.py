"""CLI entry point for the Riksarkivet TUI."""

from typing import Annotated

import typer


tui_app = typer.Typer(
    name="tui",
    help="Interactive terminal browser for the Swedish National Archives.",
)


@tui_app.command()
def tui(
    keyword: Annotated[
        str | None,
        typer.Argument(help="Optional initial search keyword"),
    ] = None,
) -> None:
    """Launch the interactive TUI for browsing Riksarkivet documents.

    Examples:
        ra tui                   # Open empty TUI
        ra tui "trolldom"        # Open with pre-filled search
        ra tui "Stockholm"       # Search for Stockholm on launch
    """
    from .app import RiksarkivetApp

    app = RiksarkivetApp(initial_keyword=keyword)
    app.run()

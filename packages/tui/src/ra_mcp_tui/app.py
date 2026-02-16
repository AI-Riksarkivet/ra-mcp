"""Main Textual application for the Riksarkivet TUI."""

from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.binding import Binding, BindingType

from .services import ArchiveService
from .widgets.help_overlay import HelpScreen


class RiksarkivetApp(App):
    """Interactive terminal browser for the Swedish National Archives."""

    TITLE = "Riksarkivet"
    SUB_TITLE = "Swedish National Archives"
    CSS_PATH = Path(__file__).parent / "styles" / "app.tcss"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit", show=True),
        Binding("question_mark", "help", "Help", show=True),
    ]

    def __init__(self, initial_keyword: str | None = None) -> None:
        super().__init__()
        self.service = ArchiveService()
        self._initial_keyword = initial_keyword

    def on_mount(self) -> None:
        from .screens.search import SearchScreen

        self.push_screen(SearchScreen(initial_keyword=self._initial_keyword))

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

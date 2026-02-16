"""Main Textual application for the Riksarkivet TUI."""

from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.binding import Binding, BindingType
from textual.theme import Theme

from .services import ArchiveService
from .widgets.help_overlay import HelpScreen

RIKSARKIVET_THEME = Theme(
    name="riksarkivet",
    primary="#BC4B6F",
    secondary="#6B9BC3",
    accent="#C9A96E",
    foreground="#E0E0EC",
    background="#0F0F1A",
    surface="#1A1A2E",
    panel="#262640",
    success="#7FB069",
    warning="#E8B649",
    error="#CF4E4E",
    dark=True,
    variables={
        "footer-foreground": "#E0E0EC",
        "footer-background": "#0F0F1A",
        "footer-key-foreground": "#0F0F1A",
        "footer-key-background": "#BC4B6F",
        "footer-description-foreground": "#9090A8",
        "input-cursor-background": "#BC4B6F",
        "input-selection-background": "#BC4B6F 30%",
        "scrollbar": "#BC4B6F 40%",
        "scrollbar-hover": "#BC4B6F 70%",
        "scrollbar-active": "#BC4B6F",
    },
)


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

        self.register_theme(RIKSARKIVET_THEME)
        self.theme = "riksarkivet"
        self.push_screen(SearchScreen(initial_keyword=self._initial_keyword))

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

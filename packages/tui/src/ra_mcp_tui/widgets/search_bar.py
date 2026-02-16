"""Search input bar with mode toggle."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Label


class ModeLabel(Label):
    """Clickable mode label that posts a Toggle message when clicked."""

    class Toggle(Message):
        """Fired when the label is clicked."""

    def on_click(self, event: Click) -> None:
        event.stop()
        self.post_message(self.Toggle())


class SearchBar(Widget):
    """Search input with transcribed/metadata mode toggle."""

    mode: reactive[str] = reactive("transcribed")

    class Submitted(Message):
        """Fired when the user submits a search query."""

        def __init__(self, keyword: str, mode: str) -> None:
            super().__init__()
            self.keyword = keyword
            self.mode = mode

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-bar"):
            yield ModeLabel(" \\[T]ranscribed ", id="mode-label")
            yield Input(placeholder="Search Riksarkivet...", id="search-input")

    def on_mount(self) -> None:
        self._update_mode_label()

    def watch_mode(self) -> None:
        self._update_mode_label()

    def _update_mode_label(self) -> None:
        label = self.query_one("#mode-label", ModeLabel)
        if self.mode == "transcribed":
            label.update(" \\[T]ranscribed ")
        else:
            label.update(" \\[M]etadata ")

    def on_mode_label_toggle(self) -> None:
        self.toggle_mode()

    def toggle_mode(self) -> None:
        """Switch between transcribed and metadata search."""
        self.mode = "metadata" if self.mode == "transcribed" else "transcribed"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        keyword = event.value.strip()
        if keyword:
            self.post_message(self.Submitted(keyword=keyword, mode=self.mode))

    def focus_input(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def set_value(self, text: str) -> None:
        """Set the input value programmatically."""
        self.query_one("#search-input", Input).value = text

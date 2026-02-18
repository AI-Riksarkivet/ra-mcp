"""Search input bar with mode toggle."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, RadioButton, RadioSet


class SearchBar(Widget):
    """Search input with transcribed/metadata mode toggle and limit selector."""

    DEFAULT_LIMIT = 100

    mode: reactive[str] = reactive("transcribed")

    class Submitted(Message):
        """Fired when the user submits a search query."""

        def __init__(self, keyword: str, mode: str, limit: int) -> None:
            super().__init__()
            self.keyword = keyword
            self.mode = mode
            self.limit = limit

    def compose(self) -> ComposeResult:
        with Horizontal(id="search-bar"):
            with RadioSet(id="mode-toggle"):
                yield RadioButton("Transcribed", value=True, id="mode-transcribed")
                yield RadioButton("Metadata", id="mode-metadata")
            yield Input(placeholder="Search Riksarkivet...  (m to toggle mode)", id="search-input")
            yield Input(str(self.DEFAULT_LIMIT), id="limit-input", type="integer")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        event.stop()
        self.mode = "transcribed" if event.pressed.id == "mode-transcribed" else "metadata"

    def toggle_mode(self) -> None:
        """Switch between transcribed and metadata search."""
        if self.mode == "transcribed":
            self.query_one("#mode-metadata", RadioButton).value = True
        else:
            self.query_one("#mode-transcribed", RadioButton).value = True

    @property
    def limit(self) -> int:
        """Current limit value."""
        try:
            return max(1, int(self.query_one("#limit-input", Input).value))
        except (ValueError, TypeError):
            return self.DEFAULT_LIMIT

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "limit-input":
            return
        keyword = event.value.strip()
        if keyword:
            self.post_message(self.Submitted(keyword=keyword, mode=self.mode, limit=self.limit))

    def focus_input(self) -> None:
        """Focus the search input."""
        self.query_one("#search-input", Input).focus()

    def set_value(self, text: str) -> None:
        """Set the input value programmatically."""
        self.query_one("#search-input", Input).value = text

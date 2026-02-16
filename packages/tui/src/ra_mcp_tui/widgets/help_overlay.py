"""Modal help overlay showing keybindings."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import BindingType
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, Static


HELP_TEXT = """\
Keybindings

  /          Focus search input
  Enter      Submit search / Open selected item
  Escape     Go back / Clear search
  m          Toggle search mode (Transcribed / Metadata)
  n / p      Next / Previous page of results
  o          Open in browser (works on all screens)
  y          Copy reference code to clipboard

  n          Next page (in page viewer)
  p          Previous page (in page viewer)
  c          Copy page text to clipboard
  a          Copy ALTO XML URL to clipboard

  ?          Show this help
  q          Quit
"""


class HelpScreen(ModalScreen[None]):
    """Modal overlay displaying keybindings reference."""

    BINDINGS: ClassVar[list[BindingType]] = [
        ("escape", "dismiss", "Close"),
        ("question_mark", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Center(), Vertical(id="help-dialog"):
            yield Static(HELP_TEXT, id="help-text")
            yield Label("Press Escape to close", id="help-hint")

    def action_dismiss(self) -> None:  # type: ignore[override]
        self.dismiss(None)

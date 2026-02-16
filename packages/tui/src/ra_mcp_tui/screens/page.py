"""Page screen — full transcription viewer with page navigation."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header

from ra_mcp_browse.models import PageContext

from ..widgets.page_viewer import PageViewer


class PageScreen(Screen):
    """Full-text page viewer with n/p navigation."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("n", "next_page", "Next", show=True),
        Binding("p", "prev_page", "Prev", show=True),
        Binding("y", "copy_ref", "Copy Ref", show=True),
    ]

    def __init__(self, page: PageContext, all_pages: list[PageContext], keyword: str) -> None:
        super().__init__()
        self._all_pages = all_pages
        self._keyword = keyword
        self._current_index = next((i for i, p in enumerate(all_pages) if p.page_number == page.page_number), 0)

    def compose(self) -> ComposeResult:
        yield Header()
        yield PageViewer(id="viewer")
        yield Footer()

    def on_mount(self) -> None:
        self._show_current_page()

    def _show_current_page(self) -> None:
        page = self._all_pages[self._current_index]
        self.query_one(PageViewer).set_page(page, self._current_index, len(self._all_pages))

    def action_next_page(self) -> None:
        if self._current_index < len(self._all_pages) - 1:
            self._current_index += 1
            self._show_current_page()

    def action_prev_page(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._show_current_page()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_copy_ref(self) -> None:
        page = self._all_pages[self._current_index]
        self.app.copy_to_clipboard(page.reference_code)
        self.notify(f"Copied: {page.reference_code}")

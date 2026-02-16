"""Page screen — full transcription viewer with page navigation."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.worker import Worker, WorkerState

from ra_mcp_browse.models import BrowseResult, PageContext

from ..widgets.page_viewer import PageViewer


if TYPE_CHECKING:
    from ..app import RiksarkivetApp

BATCH_SIZE = 20


class PageScreen(Screen):
    """Full-text page viewer with n/p navigation and automatic page loading."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("n", "next_page", "Next", show=True),
        Binding("p", "prev_page", "Prev", show=True),
        Binding("y", "copy_ref", "Copy Ref", show=True),
    ]

    def __init__(
        self,
        page: PageContext,
        all_pages: list[PageContext],
        keyword: str,
        reference_code: str,
    ) -> None:
        super().__init__()
        self._all_pages = list(all_pages)
        self._keyword = keyword
        self._reference_code = reference_code
        self._current_index = next((i for i, p in enumerate(all_pages) if p.page_number == page.page_number), 0)
        self._loading = False
        self._load_worker: Worker[BrowseResult] | None = None
        self._max_requested_page = max(p.page_number for p in all_pages) if all_pages else BATCH_SIZE

    @property
    def _service(self) -> RiksarkivetApp:
        return self.app  # type: ignore[return-value]

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
        elif not self._loading:
            self._load_more_pages()

    def action_prev_page(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._show_current_page()

    def _load_more_pages(self) -> None:
        """Fetch the next batch of pages from the API."""
        self._loading = True
        self.notify("Loading more pages...")
        start = self._max_requested_page + 1
        end = start + BATCH_SIZE - 1
        page_spec = f"{start}-{end}"
        service = self._service.service
        ref_code = self._reference_code
        keyword = self._keyword
        self._load_worker = self.run_worker(
            lambda: service.browse_document(reference_code=ref_code, pages=page_spec, highlight_term=keyword),
            thread=True,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker is not self._load_worker:
            return
        self._loading = False
        if event.state == WorkerState.SUCCESS:
            result: BrowseResult = event.worker.result  # type: ignore[assignment]
            if result.contexts:
                self._all_pages.extend(result.contexts)
                self._max_requested_page = max(p.page_number for p in result.contexts)
                self._current_index += 1
                self._show_current_page()
            else:
                self.notify("No more pages in this document")
        elif event.state == WorkerState.ERROR:
            self.notify(f"Failed to load pages: {event.worker.error}", severity="error")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_copy_ref(self) -> None:
        page = self._all_pages[self._current_index]
        self.app.copy_to_clipboard(page.reference_code)
        self.notify(f"Copied: {page.reference_code}")

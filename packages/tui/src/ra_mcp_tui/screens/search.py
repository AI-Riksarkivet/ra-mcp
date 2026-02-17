"""Search screen — root screen with search input and result list."""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.worker import Worker, WorkerState

from ra_mcp_browse.models import BrowseResult
from ra_mcp_search.models import SearchRecord, SearchResult

from ..widgets.result_list import ResultList
from ..widgets.search_bar import SearchBar


if TYPE_CHECKING:
    from ..app import RiksarkivetApp


class SearchScreen(Screen):
    """Root screen: search input + result list."""

    SUB_TITLE = "Search Archives"
    PAGE_SIZE = 25

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("slash", "focus_search", "Search", show=True),
        Binding("m", "toggle_mode", "Mode", show=True),
        Binding("d", "open_document", "Document", show=True),
        Binding("n", "next_page", "Next Page", show=True),
        Binding("p", "prev_page", "Prev Page", show=True),
        Binding("o", "open_link", "Open", show=True),
    ]

    def __init__(self, initial_keyword: str | None = None) -> None:
        super().__init__()
        self._initial_keyword = initial_keyword
        self._current_keyword = ""
        self._current_mode = "transcribed"
        self._current_offset = 0
        self._total_hits = 0
        self._current_worker: Worker[SearchResult] | None = None
        self._snippet_worker: Worker[BrowseResult] | None = None
        self._snippet_record: SearchRecord | None = None

    @property
    def _service(self) -> RiksarkivetApp:
        return self.app  # type: ignore[return-value]

    def compose(self) -> ComposeResult:
        yield Header()
        yield SearchBar()
        yield ResultList()
        yield Footer()

    def on_mount(self) -> None:
        if self._initial_keyword:
            bar = self.query_one(SearchBar)
            bar.set_value(self._initial_keyword)
            self._run_search(self._initial_keyword, bar.mode)
        else:
            self.query_one(SearchBar).focus_input()

    def on_search_bar_submitted(self, event: SearchBar.Submitted) -> None:
        self._current_offset = 0
        self._run_search(event.keyword, event.mode)

    def _run_search(self, keyword: str, mode: str, offset: int = 0) -> None:
        self._current_keyword = keyword
        self._current_mode = mode
        self._current_offset = offset
        self.query_one(ResultList).show_loading(keyword)
        if self._current_worker and self._current_worker.state == WorkerState.RUNNING:
            self._current_worker.cancel()
        service = self._service.service
        page_size = self.PAGE_SIZE
        if mode == "transcribed":
            fn = lambda: service.search_transcribed(keyword, offset=offset, max_results=page_size)  # noqa: E731
        else:
            fn = lambda: service.search_metadata(keyword, offset=offset, max_results=page_size)  # noqa: E731
        self._current_worker = self.run_worker(fn, thread=True)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker is self._current_worker:
            self._handle_search_result(event)
        elif event.worker is self._snippet_worker:
            self._handle_snippet_result(event)

    def _handle_search_result(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            result: SearchResult = event.worker.result  # type: ignore[assignment]
            self._total_hits = result.total_hits
            self.query_one(ResultList).set_results(result.items, result.total_hits, self._current_keyword, self._current_offset, self.PAGE_SIZE)
        elif event.state == WorkerState.ERROR:
            self.query_one(ResultList).set_error(str(event.worker.error))

    def _handle_snippet_result(self, event: Worker.StateChanged) -> None:
        from .page import PageScreen

        if event.state == WorkerState.SUCCESS:
            result: BrowseResult = event.worker.result  # type: ignore[assignment]
            record = self._snippet_record
            self._snippet_record = None
            if result.contexts and record:
                self.app.push_screen(
                    PageScreen(
                        page=result.contexts[0],
                        all_pages=result.contexts,
                        keyword=self._current_keyword,
                        reference_code=record.metadata.reference_code,
                    )
                )
            else:
                self.notify("Page not found")
        elif event.state == WorkerState.ERROR:
            self._snippet_record = None
            self.notify(f"Failed to load page: {event.worker.error}", severity="error")

    def action_open_document(self) -> None:
        from .document import DocumentScreen

        record = self.query_one(ResultList).get_highlighted_record()
        if record:
            self.app.push_screen(DocumentScreen(record=record, keyword=self._current_keyword))
        else:
            self.notify("No document selected")

    def on_result_list_snippet_selected(self, event: ResultList.SnippetSelected) -> None:
        self._snippet_record = event.record
        service = self._service.service
        ref_code = event.record.metadata.reference_code
        page = str(event.page_number)
        keyword = self._current_keyword
        self._snippet_worker = self.run_worker(
            lambda: service.browse_document(reference_code=ref_code, pages=page, highlight_term=keyword, max_pages=1),
            thread=True,
        )

    def action_next_page(self) -> None:
        next_offset = self._current_offset + self.PAGE_SIZE
        if self._current_keyword and next_offset < self._total_hits:
            self._run_search(self._current_keyword, self._current_mode, offset=next_offset)

    def action_prev_page(self) -> None:
        if self._current_keyword and self._current_offset > 0:
            prev_offset = max(0, self._current_offset - self.PAGE_SIZE)
            self._run_search(self._current_keyword, self._current_mode, offset=prev_offset)

    def action_open_link(self) -> None:
        link = self.query_one(ResultList).get_highlighted_link()
        if link:
            webbrowser.open(link)
            self.notify(f"Opened: {link}")
        else:
            self.notify("No link available for this item")

    def action_focus_search(self) -> None:
        self.query_one(SearchBar).focus_input()

    def action_toggle_mode(self) -> None:
        self.query_one(SearchBar).toggle_mode()

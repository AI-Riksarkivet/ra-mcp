"""Search screen — root screen with search input and result list."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.worker import Worker, WorkerState

from ra_mcp_search.models import SearchResult

from ..widgets.result_list import ResultList
from ..widgets.search_bar import SearchBar


if TYPE_CHECKING:
    from ..app import RiksarkivetApp


class SearchScreen(Screen):
    """Root screen: search input + result list."""

    PAGE_SIZE = 25

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("slash", "focus_search", "Search", show=True),
        Binding("m", "toggle_mode", "Mode", show=True),
        Binding("n", "next_page", "Next Page", show=True),
        Binding("p", "prev_page", "Prev Page", show=True),
    ]

    def __init__(self, initial_keyword: str | None = None) -> None:
        super().__init__()
        self._initial_keyword = initial_keyword
        self._current_keyword = ""
        self._current_mode = "transcribed"
        self._current_offset = 0
        self._total_hits = 0
        self._current_worker: Worker[SearchResult] | None = None

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
        if event.worker is not self._current_worker:
            return
        if event.state == WorkerState.SUCCESS:
            result: SearchResult = event.worker.result  # type: ignore[assignment]
            self._total_hits = result.total_hits
            self.query_one(ResultList).set_results(result.items, result.total_hits, self._current_keyword, self._current_offset, self.PAGE_SIZE)
        elif event.state == WorkerState.ERROR:
            self.query_one(ResultList).set_error(str(event.worker.error))

    def on_result_list_selected(self, event: ResultList.Selected) -> None:
        from .document import DocumentScreen

        self.app.push_screen(DocumentScreen(record=event.record, keyword=self._current_keyword))

    def action_next_page(self) -> None:
        next_offset = self._current_offset + self.PAGE_SIZE
        if self._current_keyword and next_offset < self._total_hits:
            self._run_search(self._current_keyword, self._current_mode, offset=next_offset)

    def action_prev_page(self) -> None:
        if self._current_keyword and self._current_offset > 0:
            prev_offset = max(0, self._current_offset - self.PAGE_SIZE)
            self._run_search(self._current_keyword, self._current_mode, offset=prev_offset)

    def action_focus_search(self) -> None:
        self.query_one(SearchBar).focus_input()

    def action_toggle_mode(self) -> None:
        self.query_one(SearchBar).toggle_mode()

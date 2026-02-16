"""Document screen — metadata + page list for a selected document."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.worker import Worker, WorkerState

from ra_mcp_browse.models import BrowseResult
from ra_mcp_search.models import SearchRecord

from ..widgets.metadata_panel import MetadataPanel
from ..widgets.result_list import PageList


if TYPE_CHECKING:
    from ..app import RiksarkivetApp


class DocumentScreen(Screen):
    """Document view: metadata panel + page list."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("y", "copy_ref", "Copy Ref", show=True),
    ]

    def __init__(self, record: SearchRecord, keyword: str) -> None:
        super().__init__()
        self._record = record
        self._keyword = keyword
        self._browse_worker: Worker[BrowseResult] | None = None

    @property
    def _service(self) -> RiksarkivetApp:
        return self.app  # type: ignore[return-value]

    def compose(self) -> ComposeResult:
        yield Header()
        yield MetadataPanel(id="doc-metadata")
        yield PageList(id="doc-pages")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(MetadataPanel).set_from_record(self._record)
        self.query_one(PageList).show_loading()
        ref_code = self._record.metadata.reference_code
        keyword = self._keyword
        service = self._service.service
        self._browse_worker = self.run_worker(
            lambda: service.browse_document(reference_code=ref_code, pages="1-20", highlight_term=keyword),
            thread=True,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker is not self._browse_worker:
            return
        if event.state == WorkerState.SUCCESS:
            result: BrowseResult = event.worker.result  # type: ignore[assignment]
            self.query_one(PageList).set_pages(result.contexts)
            if result.oai_metadata:
                self.query_one(MetadataPanel).enrich_from_oai(result.oai_metadata)
        elif event.state == WorkerState.ERROR:
            self.query_one(PageList).set_error(str(event.worker.error))

    def on_page_list_selected(self, event: PageList.Selected) -> None:
        from .page import PageScreen

        self.app.push_screen(PageScreen(page=event.page, all_pages=event.all_pages, keyword=self._keyword))

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_copy_ref(self) -> None:
        self.app.copy_to_clipboard(self._record.metadata.reference_code)
        self.notify(f"Copied: {self._record.metadata.reference_code}")

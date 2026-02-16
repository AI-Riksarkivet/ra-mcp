"""Document screen — metadata + page list for a selected document."""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual.worker import Worker, WorkerState

from ra_mcp_browse.models import BrowseResult
from ra_mcp_common.utils.formatting import page_id_to_number
from ra_mcp_search.models import SearchRecord

from ..widgets.metadata_panel import MetadataPanel
from ..widgets.result_list import PageList


if TYPE_CHECKING:
    from ..app import RiksarkivetApp

BATCH_SIZE = 20


class DocumentScreen(Screen):
    """Document view: metadata panel + page list."""

    SUB_TITLE = "Document Browser"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("o", "open_link", "Open", show=True),
        Binding("y", "copy_ref", "Copy Ref", show=True),
    ]

    def __init__(self, record: SearchRecord, keyword: str) -> None:
        super().__init__()
        self._record = record
        self._keyword = keyword
        self._browse_worker: Worker[BrowseResult] | None = None
        self._max_loaded_page = 0
        self._loading = False

    @property
    def _service(self) -> RiksarkivetApp:
        return self.app  # type: ignore[return-value]

    def compose(self) -> ComposeResult:
        yield Header()
        yield MetadataPanel(id="doc-metadata")
        yield PageList(id="doc-pages")
        yield Footer()

    def _extract_hit_pages(self) -> set[int]:
        """Extract page numbers that have search hits from the record's snippets."""
        hit_pages: set[int] = set()
        if self._record.transcribed_text:
            for snippet in self._record.transcribed_text.snippets:
                for page_info in snippet.pages:
                    hit_pages.add(page_id_to_number(page_info.id))
        return hit_pages

    def on_mount(self) -> None:
        self.query_one(MetadataPanel).set_from_record(self._record)
        page_list = self.query_one(PageList)
        page_list.set_hit_pages(self._extract_hit_pages())
        page_list.show_loading()
        self._fetch_pages(1, BATCH_SIZE)

    def _fetch_pages(self, start: int, end: int) -> None:
        self._loading = True
        page_spec = f"{start}-{end}"
        service = self._service.service
        ref_code = self._record.metadata.reference_code
        keyword = self._keyword
        self._browse_worker = self.run_worker(
            lambda: service.browse_document(reference_code=ref_code, pages=page_spec, highlight_term=keyword),
            thread=True,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker is not self._browse_worker:
            return
        self._loading = False
        if event.state == WorkerState.SUCCESS:
            result: BrowseResult = event.worker.result  # type: ignore[assignment]
            page_list = self.query_one(PageList)
            if self._max_loaded_page == 0:
                # First load
                page_list.set_pages(result.contexts)
                if result.oai_metadata:
                    self.query_one(MetadataPanel).enrich_from_oai(result.oai_metadata)
            elif result.contexts:
                page_list.append_pages(result.contexts)
            else:
                self.notify("No more pages in this document")
            if result.contexts:
                self._max_loaded_page = max(p.page_number for p in result.contexts)
        elif event.state == WorkerState.ERROR:
            self.query_one(PageList).set_error(str(event.worker.error))

    def on_page_list_near_end(self, event: PageList.NearEnd) -> None:
        if self._loading or self._max_loaded_page == 0:
            return
        start = self._max_loaded_page + 1
        end = start + BATCH_SIZE - 1
        self._fetch_pages(start, end)

    def on_page_list_selected(self, event: PageList.Selected) -> None:
        from .page import PageScreen

        self.app.push_screen(
            PageScreen(
                page=event.page,
                all_pages=event.all_pages,
                keyword=self._keyword,
                reference_code=self._record.metadata.reference_code,
            )
        )

    def action_open_link(self) -> None:
        if self._record.links and self._record.links.html:
            webbrowser.open(self._record.links.html)
            self.notify(f"Opened: {self._record.links.html}")
        else:
            self.notify("No link available for this document")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_copy_ref(self) -> None:
        self.app.copy_to_clipboard(self._record.metadata.reference_code)
        self.notify(f"Copied: {self._record.metadata.reference_code}")

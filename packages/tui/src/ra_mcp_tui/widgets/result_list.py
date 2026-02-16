"""List widgets for search results and document pages."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import DataTable, Label, LoadingIndicator

from ra_mcp_browse.models import PageContext
from ra_mcp_search.models import SearchRecord


class ResultList(Widget):
    """Displays search results as a data table with columns."""

    class Selected(Message):
        """Fired when a result is selected."""

        def __init__(self, record: SearchRecord) -> None:
            super().__init__()
            self.record = record

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._records: list[SearchRecord] = []

    def compose(self) -> ComposeResult:
        yield LoadingIndicator(id="result-loading")
        yield DataTable(id="result-table", cursor_type="row")
        yield Label("", id="result-status")

    def on_mount(self) -> None:
        self.query_one("#result-loading").display = False
        table = self.query_one("#result-table", DataTable)
        table.add_columns("Ref", "Title", "Date", "Provenance", "Type", "Hits")

    def set_results(self, records: list[SearchRecord], total_hits: int, keyword: str, offset: int = 0, page_size: int = 25) -> None:
        """Populate the table with search results."""
        self._records = records
        self.query_one("#result-loading").display = False
        table = self.query_one("#result-table", DataTable)
        table.display = True
        table.clear()
        for record in records:
            ref = record.metadata.reference_code
            title = self._truncate(record.get_title(), 50)
            date = record.metadata.date or "-"
            prov = self._get_provenance(record)
            rtype = record.type
            hits = str(record.get_total_hits())
            table.add_row(ref, title, date, prov, rtype, hits)
        status = self.query_one("#result-status", Label)
        start = offset + 1
        end = offset + len(records)
        page_info = f" {start}-{end} of {total_hits} results for '{keyword}'"
        if total_hits > page_size:
            page_num = offset // page_size + 1
            total_pages = (total_hits + page_size - 1) // page_size
            page_info += f"  (page {page_num}/{total_pages}, n/p to navigate)"
        status.update(page_info)

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        return text[:max_len - 1] + "\u2026" if len(text) > max_len else text

    @staticmethod
    def _get_provenance(record: SearchRecord) -> str:
        if record.metadata.provenance:
            return record.metadata.provenance[0].caption
        return "-"

    def show_loading(self, keyword: str) -> None:
        """Show loading state with animated indicator."""
        self.query_one("#result-table", DataTable).display = False
        self.query_one("#result-loading").display = True
        status = self.query_one("#result-status", Label)
        status.update(f" Searching for '{keyword}'...")

    def set_error(self, message: str) -> None:
        """Show error state."""
        self.query_one("#result-loading").display = False
        table = self.query_one("#result-table", DataTable)
        table.display = True
        table.clear()
        status = self.query_one("#result-status", Label)
        status.update(f" Error: {message}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_index = event.cursor_row
        if 0 <= row_index < len(self._records):
            self.post_message(self.Selected(record=self._records[row_index]))


class PageList(Widget):
    """Displays document pages as a data table."""

    AUTOLOAD_THRESHOLD = 3
    HIT_MARKER = ">>>"

    class Selected(Message):
        """Fired when a page is selected."""

        def __init__(self, page: PageContext, all_pages: list[PageContext]) -> None:
            super().__init__()
            self.page = page
            self.all_pages = all_pages

    class NearEnd(Message):
        """Fired when the cursor is near the end of the list."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._pages: list[PageContext] = []
        self._hit_pages: set[int] = set()

    def compose(self) -> ComposeResult:
        yield LoadingIndicator(id="page-loading")
        yield DataTable(id="page-table", cursor_type="row")
        yield Label("", id="page-status")

    def on_mount(self) -> None:
        self.query_one("#page-loading").display = False
        table = self.query_one("#page-table", DataTable)
        table.add_columns("Hit", "Page", "Preview")

    def set_hit_pages(self, hit_pages: set[int]) -> None:
        """Set which page numbers have search hits."""
        self._hit_pages = hit_pages

    def set_pages(self, pages: list[PageContext]) -> None:
        """Populate the table with document pages."""
        self._pages = list(pages)
        self.query_one("#page-loading").display = False
        table = self.query_one("#page-table", DataTable)
        table.display = True
        table.clear()
        for page in pages:
            self._append_page_row(table, page)
        self._update_status()

    def append_pages(self, pages: list[PageContext]) -> None:
        """Append additional pages to the existing table."""
        table = self.query_one("#page-table", DataTable)
        for page in pages:
            self._pages.append(page)
            self._append_page_row(table, page)
        self._update_status()

    def _append_page_row(self, table: DataTable, page: PageContext) -> None:
        preview = page.full_text[:120].replace("\n", " ") if page.full_text else "(empty page)"
        hit = self.HIT_MARKER if page.page_number in self._hit_pages else ""
        table.add_row(hit, str(page.page_number), preview)

    def _update_status(self) -> None:
        hit_count = sum(1 for p in self._pages if p.page_number in self._hit_pages)
        status = self.query_one("#page-status", Label)
        hit_info = f"  ({hit_count} hits)" if hit_count else ""
        status.update(f" {len(self._pages)} pages loaded{hit_info}")

    def show_loading(self) -> None:
        """Show loading state with animated indicator."""
        self.query_one("#page-table", DataTable).display = False
        self.query_one("#page-loading").display = True
        status = self.query_one("#page-status", Label)
        status.update(" Loading pages...")

    def set_error(self, message: str) -> None:
        """Show error state."""
        self.query_one("#page-loading").display = False
        self.query_one("#page-table", DataTable).display = True
        status = self.query_one("#page-status", Label)
        status.update(f" Error: {message}")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        idx = event.cursor_row
        if idx is not None and len(self._pages) - idx <= self.AUTOLOAD_THRESHOLD:
            self.post_message(self.NearEnd())

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._pages):
            self.post_message(self.Selected(page=self._pages[idx], all_pages=self._pages))

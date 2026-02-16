"""List widgets for search results and document pages."""

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView

from ra_mcp_browse.models import PageContext
from ra_mcp_search.models import SearchRecord


class ResultList(Widget):
    """Displays search results as a selectable list."""

    class Selected(Message):
        """Fired when a result is selected."""

        def __init__(self, record: SearchRecord) -> None:
            super().__init__()
            self.record = record

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._records: list[SearchRecord] = []

    def compose(self) -> ComposeResult:
        yield ListView(id="result-listview")
        yield Label("", id="result-status")

    def set_results(self, records: list[SearchRecord], total_hits: int, keyword: str, offset: int = 0, page_size: int = 25) -> None:
        """Populate the list with search results."""
        self._records = records
        listview = self.query_one("#result-listview", ListView)
        listview.clear()
        for record in records:
            ref = record.metadata.reference_code
            title = record.get_title()
            hits = record.get_total_hits()
            date = record.metadata.date or ""
            line = f"{ref}  {title}  {date}  ({hits} hits)"
            listview.append(ListItem(Label(line)))
        status = self.query_one("#result-status", Label)
        start = offset + 1
        end = offset + len(records)
        page_info = f" {start}-{end} of {total_hits} results for '{keyword}'"
        if total_hits > page_size:
            page_num = offset // page_size + 1
            total_pages = (total_hits + page_size - 1) // page_size
            page_info += f"  (page {page_num}/{total_pages}, n/p to navigate)"
        status.update(page_info)

    def show_loading(self, keyword: str) -> None:
        """Show loading state."""
        listview = self.query_one("#result-listview", ListView)
        listview.clear()
        status = self.query_one("#result-status", Label)
        status.update(f" Searching for '{keyword}'...")

    def set_error(self, message: str) -> None:
        """Show error state."""
        listview = self.query_one("#result-listview", ListView)
        listview.clear()
        status = self.query_one("#result-status", Label)
        status.update(f" Error: {message}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._records):
            self.post_message(self.Selected(record=self._records[idx]))


class PageList(Widget):
    """Displays document pages as a selectable list."""

    AUTOLOAD_THRESHOLD = 3

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
        yield ListView(id="page-listview")
        yield Label("", id="page-status")

    def set_hit_pages(self, hit_pages: set[int]) -> None:
        """Set which page numbers have search hits."""
        self._hit_pages = hit_pages

    def set_pages(self, pages: list[PageContext]) -> None:
        """Populate the list with document pages."""
        self._pages = list(pages)
        listview = self.query_one("#page-listview", ListView)
        listview.clear()
        for page in pages:
            self._append_page_item(listview, page)
        self._update_status()

    def append_pages(self, pages: list[PageContext]) -> None:
        """Append additional pages to the existing list."""
        listview = self.query_one("#page-listview", ListView)
        for page in pages:
            self._pages.append(page)
            self._append_page_item(listview, page)
        self._update_status()

    def _append_page_item(self, listview: ListView, page: PageContext) -> None:
        preview = page.full_text[:100].replace("\n", " ") if page.full_text else "(empty page)"
        marker = " << HIT" if page.page_number in self._hit_pages else ""
        line = f"Page {page.page_number}{marker}: {preview}"
        listview.append(ListItem(Label(line)))

    def _update_status(self) -> None:
        status = self.query_one("#page-status", Label)
        status.update(f" {len(self._pages)} pages loaded")

    def show_loading(self) -> None:
        """Show loading state."""
        listview = self.query_one("#page-listview", ListView)
        listview.clear()
        status = self.query_one("#page-status", Label)
        status.update(" Loading pages...")

    def set_error(self, message: str) -> None:
        """Show error state."""
        status = self.query_one("#page-status", Label)
        status.update(f" Error: {message}")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        idx = event.list_view.index
        if idx is not None and len(self._pages) - idx <= self.AUTOLOAD_THRESHOLD:
            self.post_message(self.NearEnd())

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._pages):
            self.post_message(self.Selected(page=self._pages[idx], all_pages=self._pages))

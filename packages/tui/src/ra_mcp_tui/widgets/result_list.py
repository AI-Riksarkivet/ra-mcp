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

    def set_results(self, records: list[SearchRecord], total_hits: int, keyword: str) -> None:
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
        status.update(f" {total_hits} results for '{keyword}' — showing {len(records)}")

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

    class Selected(Message):
        """Fired when a page is selected."""

        def __init__(self, page: PageContext, all_pages: list[PageContext]) -> None:
            super().__init__()
            self.page = page
            self.all_pages = all_pages

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._pages: list[PageContext] = []

    def compose(self) -> ComposeResult:
        yield ListView(id="page-listview")
        yield Label("", id="page-status")

    def set_pages(self, pages: list[PageContext]) -> None:
        """Populate the list with document pages."""
        self._pages = pages
        listview = self.query_one("#page-listview", ListView)
        listview.clear()
        for page in pages:
            preview = page.full_text[:100].replace("\n", " ") if page.full_text else "(empty page)"
            line = f"Page {page.page_number}: {preview}"
            listview.append(ListItem(Label(line)))
        status = self.query_one("#page-status", Label)
        status.update(f" {len(pages)} pages loaded")

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

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._pages):
            self.post_message(self.Selected(page=self._pages[idx], all_pages=self._pages))

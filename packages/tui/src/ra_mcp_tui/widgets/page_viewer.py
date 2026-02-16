"""Full-text transcription viewer."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, TextArea

from ra_mcp_browse.models import PageContext


class PageViewer(Widget):
    """Displays full page transcription with line numbers."""

    def compose(self) -> ComposeResult:
        yield Label("", id="page-header")
        yield TextArea("", read_only=True, show_line_numbers=True, id="page-text")
        yield Label("", id="page-links")

    def set_page(self, page: PageContext, current_index: int, total: int) -> None:
        """Display a page's transcription."""
        header = f" Page {page.page_number}  [{current_index + 1}/{total}]  Ref: {page.reference_code}"
        self.query_one("#page-header", Label).update(header)

        text = page.full_text if page.full_text else "(Empty page — no transcribed text)"
        self.query_one("#page-text", TextArea).text = text

        links = f" Image: {page.bildvisning_url}" if page.bildvisning_url else ""
        self.query_one("#page-links", Label).update(links)

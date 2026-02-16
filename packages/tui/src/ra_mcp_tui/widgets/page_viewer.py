"""Full-text transcription viewer."""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, LoadingIndicator, TextArea

from ra_mcp_browse.models import PageContext


class PageViewer(Widget):
    """Displays full page transcription with line numbers."""

    def compose(self) -> ComposeResult:
        yield Label("", id="page-header")
        yield LoadingIndicator(id="page-loading")
        yield TextArea("", read_only=True, show_line_numbers=True, id="page-text")
        yield Label("", id="page-links")

    def on_mount(self) -> None:
        self.query_one("#page-loading").display = False

    def set_page(self, page: PageContext, current_index: int, total: int) -> None:
        """Display a page's transcription."""
        header = f" Page {page.page_number}  [{current_index + 1}/{total}]  Ref: {page.reference_code}"
        self.query_one("#page-header", Label).update(header)

        self.query_one("#page-loading").display = False
        self.query_one("#page-text").display = True

        text = page.full_text if page.full_text else "(Empty page - no transcribed text)"
        self.query_one("#page-text", TextArea).text = text

        parts = []
        if page.bildvisning_url:
            parts.append(f"o: open image")
        if page.full_text:
            parts.append("c: copy text")
        if page.alto_url:
            parts.append("a: copy ALTO")
        parts.append("y: copy ref")
        self.query_one("#page-links", Label).update(f" {' | '.join(parts)}")

    def show_loading(self, message: str = "Loading pages...") -> None:
        """Show loading indicator instead of content."""
        self.query_one("#page-header", Label).update(f" {message}")
        self.query_one("#page-loading").display = True
        self.query_one("#page-text").display = False
        self.query_one("#page-links", Label).update("")

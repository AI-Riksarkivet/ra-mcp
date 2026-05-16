"""Tests for the PageViewer widget."""

from textual.app import App, ComposeResult
from textual.widgets import Label, TextArea

from ra_mcp_browse_lib.models import PageContext

from ra_mcp_tui.widgets.page_viewer import PageViewer

from conftest import REFERENCE_CODE, make_page_context


class PageViewerApp(App):
    def compose(self) -> ComposeResult:
        yield PageViewer(id="viewer")


def _label_text(label: Label) -> str:
    """Extract text content from a Textual Label."""
    return str(label.content)


async def test_page_viewer_set_page_text():
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        page = make_page_context(page_number=1, text="Transcribed content here")
        viewer.set_page(page, current_index=0, total=1)
        await pilot.pause()
        text_area = viewer.query_one("#page-text", TextArea)
        assert text_area.text == "Transcribed content here"


async def test_page_viewer_empty_page():
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        page = make_page_context(page_number=1, text="")
        viewer.set_page(page, current_index=0, total=1)
        await pilot.pause()
        text_area = viewer.query_one("#page-text", TextArea)
        assert "Empty page" in text_area.text


async def test_page_viewer_set_page_header():
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        page = make_page_context(page_number=5, text="Hello world")
        viewer.set_page(page, current_index=2, total=10)
        await pilot.pause()
        header = viewer.query_one("#page-header", Label)
        text = _label_text(header)
        assert "Page 5" in text
        assert "3/10" in text


async def test_page_viewer_show_loading():
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        viewer.show_loading("Loading more pages...")
        await pilot.pause()
        header = viewer.query_one("#page-header", Label)
        text = _label_text(header)
        assert "Loading more pages..." in text


async def test_page_viewer_loading_hides_text_area():
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        viewer.show_loading("Loading...")
        await pilot.pause()
        assert viewer.query_one("#page-text").display is False
        assert viewer.query_one("#page-loading").display is True


async def test_page_viewer_set_page_shows_text_area():
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        viewer.show_loading("Loading...")
        await pilot.pause()
        page = make_page_context(page_number=1, text="content")
        viewer.set_page(page, current_index=0, total=1)
        await pilot.pause()
        assert viewer.query_one("#page-text").display is True
        assert viewer.query_one("#page-loading").display is False


async def test_page_viewer_links_with_all_urls():
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        page = make_page_context(page_number=1, text="some text")
        viewer.set_page(page, current_index=0, total=1)
        await pilot.pause()
        links = viewer.query_one("#page-links", Label)
        link_text = _label_text(links)
        assert "o: open image" in link_text
        assert "c: copy text" in link_text
        assert "a: copy ALTO" in link_text
        assert "y: copy ref" in link_text


async def test_page_viewer_links_no_text():
    """Page without full_text should not show 'c: copy text'."""
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        page = make_page_context(page_number=1, text="")
        viewer.set_page(page, current_index=0, total=1)
        await pilot.pause()
        links = viewer.query_one("#page-links", Label)
        link_text = _label_text(links)
        assert "c: copy text" not in link_text
        assert "y: copy ref" in link_text


async def test_page_viewer_links_no_bildvisning():
    """Page without bildvisning_url should not show 'o: open image'."""
    async with PageViewerApp().run_test() as pilot:
        viewer = pilot.app.query_one(PageViewer)
        page = PageContext(
            page_number=1,
            page_id="_00001",
            reference_code=REFERENCE_CODE,
            full_text="some text",
            alto_url="https://example.com/alto.xml",
            image_url="https://example.com/img.jpg",
            bildvisning_url="",
        )
        viewer.set_page(page, current_index=0, total=1)
        await pilot.pause()
        links = viewer.query_one("#page-links", Label)
        link_text = _label_text(links)
        assert "o: open image" not in link_text

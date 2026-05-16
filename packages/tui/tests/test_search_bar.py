"""Tests for the SearchBar widget."""

from textual.app import App, ComposeResult

from ra_mcp_tui.widgets.search_bar import SearchBar


class SearchBarApp(App):
    def compose(self) -> ComposeResult:
        yield SearchBar()


async def test_search_bar_default_mode():
    async with SearchBarApp().run_test() as pilot:
        bar = pilot.app.query_one(SearchBar)
        assert bar.mode == "transcribed"


async def test_search_bar_default_limit():
    async with SearchBarApp().run_test() as pilot:
        bar = pilot.app.query_one(SearchBar)
        assert bar.limit == SearchBar.DEFAULT_LIMIT


async def test_search_bar_toggle_mode():
    async with SearchBarApp().run_test() as pilot:
        bar = pilot.app.query_one(SearchBar)
        assert bar.mode == "transcribed"
        bar.toggle_mode()
        await pilot.pause()
        assert bar.mode == "metadata"
        bar.toggle_mode()
        await pilot.pause()
        assert bar.mode == "transcribed"


async def test_search_bar_set_value():
    async with SearchBarApp().run_test() as pilot:
        bar = pilot.app.query_one(SearchBar)
        bar.set_value("trolldom")
        await pilot.pause()
        from textual.widgets import Input
        inp = bar.query_one("#search-input", Input)
        assert inp.value == "trolldom"


async def test_search_bar_submitted_message():
    async with SearchBarApp().run_test() as pilot:
        bar = pilot.app.query_one(SearchBar)
        bar.set_value("trolldom")
        await pilot.pause()
        from textual.widgets import Input
        inp = bar.query_one("#search-input", Input)
        await inp.action_submit()
        await pilot.pause()


async def test_search_bar_empty_keyword_not_submitted():
    """Empty/whitespace keywords should not trigger Submitted."""
    async with SearchBarApp().run_test() as pilot:
        bar = pilot.app.query_one(SearchBar)
        bar.set_value("   ")
        await pilot.pause()
        from textual.widgets import Input
        inp = bar.query_one("#search-input", Input)
        await inp.action_submit()
        await pilot.pause()

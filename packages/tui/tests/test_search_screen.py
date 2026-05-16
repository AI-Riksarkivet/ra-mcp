"""Tests for SearchScreen pure logic (pagination offsets)."""

from ra_mcp_tui.screens.search import SearchScreen


def test_search_screen_initial_state():
    screen = SearchScreen()
    assert screen._current_keyword == ""
    assert screen._current_mode == "transcribed"
    assert screen._current_offset == 0
    assert screen._total_hits == 0


def test_search_screen_initial_keyword():
    screen = SearchScreen(initial_keyword="trolldom")
    assert screen._initial_keyword == "trolldom"


def test_search_screen_default_limit():
    screen = SearchScreen()
    assert screen._current_limit == 100

"""Tests for the PageScreen logic (init, navigation index tracking)."""

from ra_mcp_tui.screens.page import BATCH_SIZE, PageScreen


def _make_pages(make_page_context, n: int, start: int = 1) -> list:
    return [make_page_context(page_number=i) for i in range(start, start + n)]


def test_page_screen_initial_index(make_page_context):
    pages = _make_pages(make_page_context, 5)
    screen = PageScreen(page=pages[2], all_pages=pages, keyword="test", reference_code="SE/RA/1")
    assert screen._current_index == 2


def test_page_screen_initial_index_first_page(make_page_context):
    pages = _make_pages(make_page_context, 3)
    screen = PageScreen(page=pages[0], all_pages=pages, keyword="test", reference_code="SE/RA/1")
    assert screen._current_index == 0


def test_page_screen_initial_index_last_page(make_page_context):
    pages = _make_pages(make_page_context, 5)
    screen = PageScreen(page=pages[4], all_pages=pages, keyword="test", reference_code="SE/RA/1")
    assert screen._current_index == 4


def test_page_screen_initial_index_not_found_defaults_zero(make_page_context):
    pages = _make_pages(make_page_context, 3, start=1)
    foreign_page = make_page_context(page_number=99)
    screen = PageScreen(page=foreign_page, all_pages=pages, keyword="test", reference_code="SE/RA/1")
    assert screen._current_index == 0


def test_page_screen_max_requested_page(make_page_context):
    pages = _make_pages(make_page_context, 5, start=10)
    screen = PageScreen(page=pages[0], all_pages=pages, keyword="test", reference_code="SE/RA/1")
    assert screen._max_requested_page == 14


def test_page_screen_min_requested_page(make_page_context):
    pages = _make_pages(make_page_context, 5, start=10)
    screen = PageScreen(page=pages[0], all_pages=pages, keyword="test", reference_code="SE/RA/1")
    assert screen._min_requested_page == 10


def test_page_screen_empty_pages(make_page_context):
    screen = PageScreen(page=make_page_context(1), all_pages=[], keyword="test", reference_code="SE/RA/1")
    assert screen._max_requested_page == BATCH_SIZE
    assert screen._min_requested_page == 1


def test_page_screen_copies_pages_list(make_page_context):
    """The screen should work on its own copy of the pages list."""
    pages = _make_pages(make_page_context, 3)
    screen = PageScreen(page=pages[0], all_pages=pages, keyword="test", reference_code="SE/RA/1")
    pages.append(make_page_context(page_number=99))
    assert len(screen._all_pages) == 3

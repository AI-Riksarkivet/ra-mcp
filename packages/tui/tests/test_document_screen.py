"""Tests for DocumentScreen pure logic."""

from ra_mcp_search_lib.models import PageInfo, Snippet, TranscribedText

from ra_mcp_tui.screens.document import BATCH_SIZE, DocumentScreen

from conftest import make_search_record


def test_batch_size_constant():
    assert BATCH_SIZE == 20


def test_extract_hit_pages_with_snippets():
    record = make_search_record(
        snippets=[
            Snippet(text="hit1", score=1.0, pages=[PageInfo(id="_00007")]),
            Snippet(text="hit2", score=0.8, pages=[PageInfo(id="_00012")]),
            Snippet(text="hit3", score=0.5, pages=[PageInfo(id="_00007")]),
        ],
        num_total=3,
    )
    screen = DocumentScreen(record=record, keyword="test")
    hit_pages = screen._extract_hit_pages()
    assert hit_pages == {7, 12}


def test_extract_hit_pages_no_transcribed_text():
    record = make_search_record(snippets=[], num_total=0)
    record.transcribed_text = None
    screen = DocumentScreen(record=record, keyword="test")
    assert screen._extract_hit_pages() == set()


def test_extract_hit_pages_empty_snippets():
    record = make_search_record(snippets=[], num_total=0)
    screen = DocumentScreen(record=record, keyword="test")
    assert screen._extract_hit_pages() == set()


def test_extract_hit_pages_compound_page_ids():
    record = make_search_record(
        snippets=[
            Snippet(text="hit", score=1.0, pages=[PageInfo(id="_H0000459_00005")]),
        ],
        num_total=1,
    )
    screen = DocumentScreen(record=record, keyword="test")
    assert screen._extract_hit_pages() == {5}

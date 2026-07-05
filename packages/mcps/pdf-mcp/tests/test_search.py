"""Tests for ra_mcp_pdf_mcp.search."""

import pytest

from ra_mcp_pdf_mcp.search import _count_occurrences, html_to_text, search_pages


# ── html_to_text ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "html,expected",
    [
        pytest.param("<p>Hello world</p>", "Hello world", id="simple-p"),
        pytest.param("<p>Bold <b>text</b> here</p>", "Bold  text  here", id="nested-tags"),
        pytest.param("", "", id="empty"),
        pytest.param("no tags at all", "no tags at all", id="no-html"),
        pytest.param("<div><span>nested</span></div>", "nested", id="deeply-nested"),
        pytest.param("<p>a &amp; b</p>", "a &amp; b", id="html-entities-passthrough"),
    ],
)
def test_html_to_text(html, expected):
    assert html_to_text(html) == expected


# ── _count_occurrences ───────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,term,expected",
    [
        pytest.param("hello world", "hello", 1, id="single-match"),
        pytest.param("aaa", "a", 3, id="non-overlapping-single-char"),
        pytest.param("abcabc", "abc", 2, id="repeated"),
        pytest.param("nothing here", "xyz", 0, id="no-match"),
        pytest.param("", "x", 0, id="empty-text"),
        pytest.param("stockholm stockholm stockholm", "stockholm", 3, id="triple"),
    ],
)
def test_count_occurrences(text, term, expected):
    assert _count_occurrences(text, term) == expected


# ── search_pages ─────────────────────────────────────────────────────


def test_search_pages_finds_term(sample_pages):
    result = search_pages(sample_pages, "Stockholm")
    assert result.total_matches >= 1
    page_nums = [pm.page_num for pm in result.page_matches]
    assert 1 in page_nums


def test_search_pages_case_insensitive(sample_pages):
    lower = search_pages(sample_pages, "stockholm")
    upper = search_pages(sample_pages, "STOCKHOLM")
    assert lower.total_matches == upper.total_matches
    assert lower.total_matches > 0


def test_search_pages_no_match(sample_pages):
    result = search_pages(sample_pages, "xyznonexistent")
    assert result.total_matches == 0
    assert result.page_matches == []


def test_search_pages_multiple_pages(sample_pages):
    result = search_pages(sample_pages, "Stockholm")
    page_indices = [pm.page_index for pm in result.page_matches]
    assert 0 in page_indices
    assert 2 in page_indices


def test_search_pages_counts_multiple_occurrences_in_block(sample_pages):
    result = search_pages(sample_pages, "Stockholm")
    page_2 = next(pm for pm in result.page_matches if pm.page_index == 2)
    assert page_2.match_count == 3


def test_search_pages_strips_html_before_matching(sample_pages):
    result = search_pages(sample_pages, "beslut")
    assert result.total_matches == 1
    block = result.page_matches[0].blocks[0]
    assert "<b>" not in block.text


def test_search_pages_skips_empty_html(sample_pages):
    result = search_pages(sample_pages, "Figure")
    assert result.total_matches == 0


def test_search_pages_truncates_block_text():
    long_text = "x" * 500
    pages = [
        {
            "page": 0,
            "bbox": [0, 0, 595, 842],
            "children": [
                {"html": f"<p>{long_text}</p>", "bbox": [0, 0, 100, 50], "block_type": "Text"},
            ],
        }
    ]
    result = search_pages(pages, "x")
    assert len(result.page_matches[0].blocks[0].text) <= 300


def test_search_pages_empty_input():
    result = search_pages([], "term")
    assert result.total_matches == 0
    assert result.page_matches == []


def test_search_pages_preserves_bbox(sample_pages):
    result = search_pages(sample_pages, "Kungliga")
    block = result.page_matches[0].blocks[0]
    assert block.bbox == [72, 100, 400, 130]
    assert block.block_type == "SectionHeader"

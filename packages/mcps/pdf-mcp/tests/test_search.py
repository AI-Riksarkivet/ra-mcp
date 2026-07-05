"""Tests for ra_mcp_pdf_mcp.search."""

import pytest

from ra_mcp_pdf_mcp.search import _count_occurrences, html_to_text


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

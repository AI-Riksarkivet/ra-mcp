"""Tests for page range parsing utilities."""

import pytest

from ra_mcp_browse_lib.utils import parse_page_range


def test_parse_page_range_single():
    assert parse_page_range("5") == [5]


def test_parse_page_range_range():
    assert parse_page_range("1-3") == [1, 2, 3]


def test_parse_page_range_combo():
    assert parse_page_range("1-3,5,7-9") == [1, 2, 3, 5, 7, 8, 9]


def test_parse_page_range_none_default():
    result = parse_page_range(None, total_pages=25)
    assert result == list(range(1, 21))


def test_parse_page_range_none_small_total():
    result = parse_page_range(None, total_pages=5)
    assert result == [1, 2, 3, 4, 5]


def test_parse_page_range_capped():
    result = parse_page_range("1-100", total_pages=10)
    assert result == list(range(1, 11))


def test_parse_page_range_dedup():
    assert parse_page_range("1,1,2") == [1, 2]


def test_parse_page_range_sorted():
    assert parse_page_range("5,1,3") == [1, 3, 5]


def test_parse_page_range_invalid_raises():
    with pytest.raises(ValueError, match="Invalid page specification"):
        parse_page_range("abc")


def test_parse_page_range_inverted_range_raises():
    """An inverted range like '5-1' must error clearly, not silently return []."""
    with pytest.raises(ValueError, match=r"start \(5\) must be less than or equal to end \(1\)"):
        parse_page_range("5-1")


def test_parse_page_range_empty_string_default():
    result = parse_page_range("", total_pages=5)
    assert result == [1, 2, 3, 4, 5]


def test_parse_page_range_out_of_range_ignored():
    """Pages beyond total_pages are silently dropped."""
    result = parse_page_range("5,50", total_pages=10)
    assert result == [5]


def test_parse_page_range_high_pages_within_default_cap():
    """Pages in the thousands (large church books) are kept under the default cap,
    not silently dropped as they were under the old 1000 cap."""
    assert parse_page_range("1200") == [1200]
    assert parse_page_range("1100-1102") == [1100, 1101, 1102]


@pytest.mark.parametrize(
    "page_range,total,expected",
    [
        pytest.param("1", 100, [1], id="single-page"),
        pytest.param("1-3", 100, [1, 2, 3], id="simple-range"),
        pytest.param("1,3,5", 100, [1, 3, 5], id="comma-list"),
        pytest.param("1-2,4-5", 100, [1, 2, 4, 5], id="multi-range"),
    ],
)
def test_parse_page_range_parametrized(page_range, total, expected):
    assert parse_page_range(page_range, total) == expected

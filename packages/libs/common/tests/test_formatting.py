"""Tests for shared formatting utilities."""

import pytest

from ra_mcp_common.formatting import (
    format_error_message,
    format_example_browse_command,
    highlight_keyword_markdown,
    iiif_manifest_to_bildvisaren,
    page_id_to_number,
    trim_page_number,
    trim_page_numbers,
    truncate_text,
)


# ---------------------------------------------------------------------------
# page_id_to_number
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "page_id,expected",
    [
        pytest.param("_00066", 66, id="standard"),
        pytest.param("_H0000459_00005", 5, id="compound"),
        pytest.param("_00000", 0, id="all-zeros"),
        pytest.param("_00001", 1, id="single-digit"),
        pytest.param("_12345", 12345, id="no-leading-zeros"),
        pytest.param("_0100", 100, id="middle-zeros"),
    ],
)
def test_page_id_to_number(page_id, expected):
    assert page_id_to_number(page_id) == expected


# ---------------------------------------------------------------------------
# trim_page_number / trim_page_numbers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "page_number,expected",
    [
        pytest.param("_00066", "66", id="standard"),
        pytest.param("_00000", "0", id="all-zeros"),
        pytest.param("_00001", "1", id="single"),
        pytest.param("_100", "100", id="no-leading-zeros"),
        pytest.param("__00042", "42", id="double-underscore"),
        pytest.param("0", "0", id="bare-zero"),
    ],
)
def test_trim_page_number(page_number, expected):
    assert trim_page_number(page_number) == expected


def test_trim_page_numbers():
    assert trim_page_numbers(["_007", "_042", "_00000"]) == ["7", "42", "0"]


def test_trim_page_numbers_empty():
    assert trim_page_numbers([]) == []


# ---------------------------------------------------------------------------
# iiif_manifest_to_bildvisaren
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "manifest_url,expected",
    [
        pytest.param(
            "https://lbiiif.riksarkivet.se/arkis!R0002497/manifest",
            "https://sok.riksarkivet.se/bildvisning/R0002497",
            id="standard",
        ),
        pytest.param(
            "https://lbiiif.riksarkivet.se/arkis!A0068611_00066/manifest",
            "https://sok.riksarkivet.se/bildvisning/A0068611_00066",
            id="with-page-suffix",
        ),
        pytest.param(
            "https://some-other-url.com/data",
            "",
            id="non-matching-url",
        ),
        pytest.param(
            "",
            "",
            id="empty-string",
        ),
        pytest.param(
            "https://lbiiif.riksarkivet.se/other!R0002497/manifest",
            "",
            id="no-arkis-prefix",
        ),
        pytest.param(
            "https://lbiiif.riksarkivet.se/arkis!R0002497/other",
            "",
            id="no-manifest-suffix",
        ),
    ],
)
def test_iiif_manifest_to_bildvisaren(manifest_url, expected):
    assert iiif_manifest_to_bildvisaren(manifest_url) == expected


# ---------------------------------------------------------------------------
# truncate_text
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,max_length,add_ellipsis,expected",
    [
        pytest.param("hello", 10, True, "hello", id="short-text"),
        pytest.param("hello world", 5, True, "he...", id="with-ellipsis"),
        pytest.param("hello world", 5, False, "hello", id="no-ellipsis"),
        pytest.param("hello", 5, True, "hello", id="exact-length"),
        pytest.param("hello world", 3, True, "hel", id="max-equals-ellipsis-length"),
        pytest.param("hello world", 2, True, "he", id="max-below-ellipsis-length"),
        pytest.param("", 5, True, "", id="empty-text"),
    ],
)
def test_truncate_text(text, max_length, add_ellipsis, expected):
    assert truncate_text(text, max_length, add_ellipsis) == expected


# ---------------------------------------------------------------------------
# format_error_message
# ---------------------------------------------------------------------------


def test_format_error_message_simple():
    result = format_error_message("Something went wrong")
    assert "Something went wrong" in result
    assert "⚠️" in result


def test_format_error_message_with_suggestions():
    result = format_error_message("No results", ["Try broader terms", "Check spelling"])
    assert "No results" in result
    assert "**Suggestions**" in result
    assert "- Try broader terms" in result
    assert "- Check spelling" in result


def test_format_error_message_no_suggestions():
    result = format_error_message("Error", None)
    assert "Suggestions" not in result


def test_format_error_message_empty_suggestions():
    result = format_error_message("Error", [])
    assert "Suggestions" not in result


# ---------------------------------------------------------------------------
# format_example_browse_command
# ---------------------------------------------------------------------------


def test_format_browse_command_single_page():
    result = format_example_browse_command("SE/RA/310187/1", ["7"])
    assert result == 'ra browse "SE/RA/310187/1" --page 7'


def test_format_browse_command_multiple_pages():
    result = format_example_browse_command("SE/RA/310187/1", ["7", "8", "52"])
    assert result == 'ra browse "SE/RA/310187/1" --page "7,8,52"'


def test_format_browse_command_with_search_term():
    result = format_example_browse_command("SE/RA/310187/1", ["7"], "trolldom")
    assert '--search-term "trolldom"' in result


def test_format_browse_command_no_pages():
    assert format_example_browse_command("SE/RA/310187/1", []) == ""


def test_format_browse_command_max_five_pages():
    pages = ["1", "2", "3", "4", "5", "6", "7"]
    result = format_example_browse_command("REF", pages)
    assert "1,2,3,4,5" in result
    assert "6" not in result


# ---------------------------------------------------------------------------
# highlight_keyword_markdown
# ---------------------------------------------------------------------------


def test_highlight_keyword_markdown_basic():
    result = highlight_keyword_markdown("The court found trolldom guilty", "trolldom")
    assert result == "The court found **trolldom** guilty"


def test_highlight_keyword_markdown_case_insensitive():
    result = highlight_keyword_markdown("TROLLDOM was accused", "trolldom")
    assert result == "**TROLLDOM** was accused"


def test_highlight_keyword_markdown_already_highlighted():
    text = "The **trolldom** case was found"
    assert highlight_keyword_markdown(text, "trolldom") == text


def test_highlight_keyword_markdown_empty_keyword():
    text = "Some text here"
    assert highlight_keyword_markdown(text, "") == text


def test_highlight_keyword_markdown_no_match():
    text = "Nothing to see here"
    assert highlight_keyword_markdown(text, "trolldom") == text


def test_highlight_keyword_markdown_multiple_occurrences():
    result = highlight_keyword_markdown("trolldom and more trolldom", "trolldom")
    assert result == "**trolldom** and more **trolldom**"


def test_highlight_keyword_markdown_special_regex_chars():
    result = highlight_keyword_markdown("value is (test)", "(test)")
    assert result == "value is **(test)**"

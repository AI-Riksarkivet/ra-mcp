"""Tests for URL generation utilities."""

import pytest

from ra_mcp_browse.url_generator import (
    alto_url,
    bildvisning_url,
    format_page_number,
    iiif_image_url,
    remove_arkis_prefix,
)


# ── remove_arkis_prefix ─────────────────────────────────────────────


def test_remove_arkis_prefix():
    assert remove_arkis_prefix("arkis!R0001203") == "R0001203"


def test_remove_arkis_prefix_noop():
    assert remove_arkis_prefix("R0001203") == "R0001203"


def test_remove_arkis_prefix_empty():
    assert remove_arkis_prefix("") == ""


# ── format_page_number ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "page_number,expected",
    [
        pytest.param("5", "00005", id="bare-digit"),
        pytest.param("_5", "00005", id="underscore-prefix"),
        pytest.param("123", "00123", id="multi-digit"),
        pytest.param("00005", "00005", id="already-padded"),
        pytest.param("_00066", "00066", id="underscore-padded"),
    ],
)
def test_format_page_number(page_number, expected):
    assert format_page_number(page_number) == expected


# ── alto_url ────────────────────────────────────────────────────────


def test_alto_url():
    result = alto_url("R0001203", "7")
    assert result == "https://sok.riksarkivet.se/dokument/alto/R000/R0001203/R0001203_00007.xml"


def test_alto_url_short_manifest_returns_none():
    assert alto_url("R00", "1") is None


def test_alto_url_with_padded_page():
    result = alto_url("R0001203", "_00012")
    assert result == "https://sok.riksarkivet.se/dokument/alto/R000/R0001203/R0001203_00012.xml"


# ── iiif_image_url ──────────────────────────────────────────────────


def test_iiif_image_url():
    result = iiif_image_url("R0001203", "5")
    assert result == "https://lbiiif.riksarkivet.se/arkis!R0001203_00005/full/max/0/default.jpg"


def test_iiif_image_url_strips_arkis_prefix():
    result = iiif_image_url("arkis!R0001203", "5")
    assert result == "https://lbiiif.riksarkivet.se/arkis!R0001203_00005/full/max/0/default.jpg"


# ── bildvisning_url ─────────────────────────────────────────────────


def test_bildvisning_url():
    result = bildvisning_url("R0001203", "7")
    assert result == "https://sok.riksarkivet.se/bildvisning/R0001203_00007"


def test_bildvisning_url_with_search_term():
    result = bildvisning_url("R0001203", "7", "trolldom")
    assert result == "https://sok.riksarkivet.se/bildvisning/R0001203_00007#?q=trolldom"


def test_bildvisning_url_strips_arkis_prefix():
    result = bildvisning_url("arkis!R0001203", "7")
    assert result == "https://sok.riksarkivet.se/bildvisning/R0001203_00007"


def test_bildvisning_url_search_term_none():
    result = bildvisning_url("R0001203", "7", None)
    assert "#?q=" not in result


def test_bildvisning_url_search_term_empty():
    result = bildvisning_url("R0001203", "7", "  ")
    assert "#?q=" not in result

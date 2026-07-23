"""Tests for ra-mcp-search-mcp tools."""

import pytest
from fastmcp import Client

from ra_mcp_search_mcp.search_tool import _looks_like_reference_code, _validate_search_input
from ra_mcp_search_mcp.tools import search_mcp


def test_search_mcp_has_name() -> None:
    assert search_mcp.name == "ra-search-mcp"


async def test_transcribed_rejects_malformed_query() -> None:
    """A broken Boolean query must be rejected up front, not sent to the API."""
    async with Client(search_mcp) as client:
        result = await client.call_tool("transcribed", {"keyword": "(((", "offset": 0})
    assert "Unbalanced" in result.content[0].text


async def test_transcribed_rejects_oversized_limit() -> None:
    """An absurd limit is bounded client-side with a clear message, not an opaque HTTP 400."""
    async with Client(search_mcp) as client:
        result = await client.call_tool("transcribed", {"keyword": "Stockholm", "offset": 0, "limit": 999999})
    assert "limit must be <=" in result.content[0].text


# Archival reference codes must not be sent to the free-text search API: the API
# tokenizes them (SE, RA, single letters like "F II a") and OR-matches ~the entire
# 11M-record catalog, producing 14s / 14MB responses with useless results.
# See systematic-debugging session: reference codes are looked up via browse_document.
@pytest.mark.parametrize(
    "keyword",
    [
        pytest.param("SE/RA/25.3", id="ra-dotted"),
        pytest.param("SE/RA/25.3/13", id="ra-dotted-volume"),
        pytest.param("SE/RA/420422", id="ra-numeric"),
        pytest.param("SE/LLA/10933/F II a", id="lla-series-with-spaces"),
        pytest.param("SE/HLA/1340037/D I", id="hla-series"),
        pytest.param("SE/RA/221/2210.01.1/E/E 1/E 1 A/j/21", id="deep-hierarchy"),
        pytest.param("SE/RA/310187/1", id="ra-volume"),
        pytest.param("se/ra/420422", id="lowercase"),
        pytest.param("  SE/RA/25.3  ", id="surrounding-whitespace"),
        # Validated against 303K distinct codes extracted from NAD EAD XML (nad-mcp/.data):
        pytest.param("SE/O258G/GSA/1061", id="municipal-institution-with-digits"),
        pytest.param("SE/ÖLA/10123", id="non-ascii-institution"),
        pytest.param("SE/KrA/0022/1", id="mixed-case-institution"),
        pytest.param("SE/RA", id="bare-institution-prefix"),
        pytest.param("SE/GLA", id="bare-institution-prefix-2"),
        pytest.param("SE/902002", id="numeric-second-segment"),
        pytest.param("SE/RA/", id="bare-prefix-trailing-slash"),
    ],
)
def test_reference_code_is_detected(keyword: str) -> None:
    assert _looks_like_reference_code(keyword) is True


@pytest.mark.parametrize(
    "keyword",
    [
        pytest.param("Wallenberg", id="single-name"),
        pytest.param("trolldom", id="single-word"),
        pytest.param("Diplomatica Hollandica", id="two-words"),
        pytest.param("Stockholm handel sjöfart", id="phrase"),
        pytest.param("1783 AND (Amerika OR USA)", id="boolean-query"),
        pytest.param("km/h", id="slash-not-reference"),
        pytest.param("Sverige", id="starts-with-se-no-slash"),
        pytest.param("stockholm~1", id="fuzzy"),
        # Quoted reference codes are exact-phrase searches — a working, useful
        # pattern for enumerating an archive's child volumes (e.g. 48 hits in
        # 0.6s for "SE/RA/720660"). They must NOT be blocked.
        pytest.param('"SE/RA/720660"', id="quoted-reference-code"),
        pytest.param('"SE/RA/25.3/13"', id="quoted-reference-code-volume"),
        # Prose run-ins found in real NAD descriptions — text, not codes; must stay searchable:
        pytest.param("SE/Admavdelning", id="prose-long-segment"),
        pytest.param("SE/anvisningar", id="prose-long-segment-2"),
        pytest.param("SE/IA:-", id="prose-label-with-punctuation"),
    ],
)
def test_normal_keyword_is_not_reference_code(keyword: str) -> None:
    assert _looks_like_reference_code(keyword) is False


def test_validate_search_input_rejects_reference_code_with_alternatives() -> None:
    error = _validate_search_input("SE/RA/25.3", offset=0, year_min=None, year_max=None)
    assert error is not None
    assert "browse_document" in error
    # Must offer the quoted-phrase escape hatch, which does work against the API
    assert '"SE/RA/25.3"' in error


def test_validate_search_input_accepts_normal_keyword() -> None:
    assert _validate_search_input("Wallenberg", offset=0, year_min=None, year_max=None) is None

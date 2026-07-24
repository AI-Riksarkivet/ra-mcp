"""Tests for ra-mcp-search-mcp tools."""

import pytest
from fastmcp import Client

from ra_mcp_search_mcp.search_tool import _looks_like_boolean_query, _looks_like_reference_code, _validate_search_input
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


# The API has no boolean query parser: AND/OR/NOT are matched as literal words.
# Verified against the live API (2026-07-24): 'xyzzyqq AND smitta' → 1,642,572
# hits while 'xyzzyqq' alone → 0 ('and' alone matches 1.63M transcribed volumes
# — HTR noise plus names like "And." for Anders). Space-separated terms are
# already a conjunction ('pest smitta' = 33 = 'pest + smitta'), and '|' is
# silently dropped, so there is no OR syntax at all — OR must become separate
# searches. Wildcards (*), fuzzy (~N) and quoted phrases DO work.
@pytest.mark.parametrize(
    "keyword",
    [
        pytest.param("pest AND smitta", id="word-and"),
        pytest.param("(pest~1 AND smitta~1)", id="word-and-fuzzy-parens"),
        pytest.param("kaffe OR caffe", id="word-or"),
        pytest.param("(häxprocess OR trolldomsmål)", id="word-or-parens"),
        pytest.param("smitta NOT venerisk", id="word-not"),
        pytest.param("pest | smitta", id="pipe"),
    ],
)
def test_boolean_syntax_is_detected(keyword: str) -> None:
    assert _looks_like_boolean_query(keyword) is True


@pytest.mark.parametrize(
    "keyword",
    [
        pytest.param("pest smitta", id="space-separated-conjunction"),
        pytest.param("trolldom~1", id="fuzzy"),
        pytest.param("trolldo*", id="wildcard"),
        pytest.param('"pest smitta"', id="quoted-phrase"),
        pytest.param('"pest AND smitta"', id="quoted-phrase-containing-operator"),
        # Lowercase and/or/not are real Swedish words (and = duck, not = seine
        # net) and must stay searchable; only the uppercase operator idiom is blocked.
        pytest.param("and", id="lowercase-and-is-swedish"),
        pytest.param("not", id="lowercase-not-is-swedish"),
        pytest.param("Anders och Greta", id="swedish-conjunction"),
        pytest.param("GRAND HOTEL", id="uppercase-word-containing-and"),
        pytest.param("NOTARIUS PUBLICUS", id="uppercase-word-starting-with-not"),
    ],
)
def test_normal_keyword_is_not_boolean_syntax(keyword: str) -> None:
    assert _looks_like_boolean_query(keyword) is False


def test_validate_search_input_rejects_boolean_query_with_alternatives() -> None:
    error = _validate_search_input("pest AND smitta", offset=0, year_min=None, year_max=None)
    assert error is not None
    # Must teach the syntax that actually works: plain terms are ANDed already,
    # and OR has to become separate searches.
    assert "pest smitta" in error
    assert "separate" in error.lower()


def test_validate_search_input_accepts_space_separated_terms() -> None:
    assert _validate_search_input("pest smitta", offset=0, year_min=None, year_max=None) is None


# Quoted phrases never match in transcribed search: "Venerisk smitta" occurs
# verbatim and adjacent in SE/HLA/1070112/B/B I/2 page 392, yet
# transcribed_text="venerisk smitta" (any casing) returns 0 while the unquoted
# pair returns 34 (verified 2026-07-24). On the metadata field, quotes DO match
# reference codes ("SE/RA/720660" → 48 child volumes) but not title phrases
# ("Handlingar till brevdiariet" → 0 despite being a verbatim title).
@pytest.mark.parametrize(
    "keyword",
    [
        pytest.param('"venerisk smitta"', id="quoted-phrase"),
        pytest.param('"SE/RA/720660"', id="quoted-reference-code"),
    ],
)
def test_transcribed_rejects_quoted_keyword(keyword: str) -> None:
    error = _validate_search_input(keyword, offset=0, year_min=None, year_max=None, transcribed=True)
    assert error is not None
    assert "quote" in error.lower()


def test_metadata_accepts_quoted_reference_code() -> None:
    assert _validate_search_input('"SE/RA/720660"', offset=0, year_min=None, year_max=None) is None


def test_validate_search_input_rejects_reference_code_with_alternatives() -> None:
    error = _validate_search_input("SE/RA/25.3", offset=0, year_min=None, year_max=None)
    assert error is not None
    assert "browse_document" in error
    # The quoted-code lookup only works in metadata search — the suggestion must say so
    assert '"SE/RA/25.3"' in error
    assert "search_metadata" in error


def test_validate_search_input_accepts_normal_keyword() -> None:
    assert _validate_search_input("Wallenberg", offset=0, year_min=None, year_max=None) is None

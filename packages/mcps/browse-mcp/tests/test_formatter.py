"""Tests for the browse-mcp ``PlainTextFormatter``.

Formatters are pure sync functions (record/result models -> markdown/text
string), so these are plain sync tests with no network, LanceDB, mocks, or
telemetry. Sample records are built from the real pydantic models the
formatter reads (search-lib ``SearchResult``, browse-lib ``BrowseResult``,
oai-pmh-lib ``OAIPMHMetadata``).
"""

from ra_mcp_browse_lib.models import BrowseResult, PageContext
from ra_mcp_browse_mcp.formatter import PlainTextFormatter
from ra_mcp_oai_pmh_lib import OAIPMHMetadata
from ra_mcp_search_lib.models import (
    RecordsResponse,
    SearchRecord,
    SearchResult,
)


# ---------------------------------------------------------------------------
# Factories for realistic sample records
# ---------------------------------------------------------------------------

REF_CODE = "SE/RA/310187/1"
MANIFEST_ID = "R0001203"


def _search_result(records: list[SearchRecord], *, keyword: str = "Stockholm", limit: int = 20, offset: int = 0, total_hits: int = 100) -> SearchResult:
    return SearchResult(
        response=RecordsResponse(items=records, totalHits=total_hits),
        transcribed_text=keyword,
        limit=limit,
        offset=offset,
    )


def _page_context(
    page_number: int,
    *,
    text: str = "Detta är transkriberad text",
    image: bool = True,
    bildvisning: bool = True,
) -> PageContext:
    return PageContext(
        page_number=page_number,
        page_id=f"{MANIFEST_ID}_{page_number:05d}",
        reference_code=REF_CODE,
        full_text=text,
        alto_url=f"https://sok.riksarkivet.se/dokument/alto/{MANIFEST_ID}/{MANIFEST_ID}_{page_number:05d}.xml",
        image_url=f"https://lbiiif.riksarkivet.se/arkis!{MANIFEST_ID}_{page_number:05d}/full/max/0/default.jpg" if image else "",
        bildvisning_url=f"https://sok.riksarkivet.se/bildvisning/{MANIFEST_ID}_{page_number:05d}" if bildvisning else "",
    )


# ---------------------------------------------------------------------------
# highlight_search_keyword
# ---------------------------------------------------------------------------


def test_highlight_search_keyword_wraps_match_in_bold():
    fmt = PlainTextFormatter()
    out = fmt.highlight_search_keyword("Anna bor i Stockholm", "Stockholm")
    assert "**Stockholm**" in out


def test_highlight_search_keyword_is_case_insensitive():
    fmt = PlainTextFormatter()
    out = fmt.highlight_search_keyword("resa till STOCKHOLM idag", "stockholm")
    assert "**STOCKHOLM**" in out


def test_highlight_search_keyword_preserves_existing_markers():
    fmt = PlainTextFormatter()
    # Text already contains ** markers from the API -> returned unchanged.
    text = "handel i **Stockholm** stad"
    assert fmt.highlight_search_keyword(text, "Stockholm") == text


def test_highlight_search_keyword_empty_keyword_returns_original():
    fmt = PlainTextFormatter()
    assert fmt.highlight_search_keyword("no keyword here", "") == "no keyword here"


# ---------------------------------------------------------------------------
# format_no_results_message
# ---------------------------------------------------------------------------


def test_format_no_results_message_offset_zero():
    fmt = PlainTextFormatter()
    result = _search_result([], keyword="trolldom", offset=0)
    out = fmt.format_no_results_message(result)
    assert "No results found for 'trolldom'" in out


def test_format_no_results_message_with_offset():
    fmt = PlainTextFormatter()
    result = _search_result([], keyword="trolldom", offset=20, total_hits=5)
    out = fmt.format_no_results_message(result)
    assert "No more results found for 'trolldom' at offset 20" in out
    assert "Total results: 5" in out


# ---------------------------------------------------------------------------
# format_browse_results
# ---------------------------------------------------------------------------


def test_format_browse_results_no_contexts_no_metadata():
    fmt = PlainTextFormatter()
    result = BrowseResult(contexts=[], reference_code=REF_CODE, pages_requested="1-5")
    out = fmt.format_browse_results(result)
    assert out == f"No page contexts found for {REF_CODE}"


def test_format_browse_results_single_context():
    fmt = PlainTextFormatter()
    result = BrowseResult(contexts=[_page_context(7)], reference_code=REF_CODE, pages_requested="7")
    out = fmt.format_browse_results(result)

    assert f"📚 Document: {REF_CODE}" in out
    assert "📖 Pages loaded: 1" in out
    assert "📄 Page 7" in out
    assert "Detta är transkriberad text" in out
    assert "🔗 Links:" in out
    assert "📝 ALTO XML: https://sok.riksarkivet.se/dokument/alto/" in out
    assert "🖼️  Image: https://lbiiif.riksarkivet.se/arkis!" in out
    assert "👁️  Bildvisning: https://sok.riksarkivet.se/bildvisning/" in out
    assert "Tip:" in out


def test_format_browse_results_multiple_contexts():
    fmt = PlainTextFormatter()
    result = BrowseResult(
        contexts=[_page_context(7), _page_context(8)],
        reference_code=REF_CODE,
        pages_requested="7-8",
    )
    out = fmt.format_browse_results(result)
    assert "📖 Pages loaded: 2" in out
    assert "📄 Page 7" in out
    assert "📄 Page 8" in out


def test_format_browse_results_empty_page_text():
    fmt = PlainTextFormatter()
    result = BrowseResult(contexts=[_page_context(3, text="   ")], reference_code=REF_CODE, pages_requested="3")
    out = fmt.format_browse_results(result)
    assert "(Empty page - no transcribed text)" in out


def test_format_browse_results_highlights_term():
    fmt = PlainTextFormatter()
    result = BrowseResult(
        contexts=[_page_context(7, text="resan till Stockholm var lång")],
        reference_code=REF_CODE,
        pages_requested="7",
    )
    out = fmt.format_browse_results(result, highlight_term="Stockholm")
    assert "**Stockholm**" in out


def test_format_browse_results_omits_missing_image_and_bildvisning():
    fmt = PlainTextFormatter()
    result = BrowseResult(
        contexts=[_page_context(7, image=False, bildvisning=False)],
        reference_code=REF_CODE,
        pages_requested="7",
    )
    out = fmt.format_browse_results(result)
    assert "📝 ALTO XML:" in out
    assert "🖼️  Image:" not in out
    assert "👁️  Bildvisning:" not in out


def test_format_browse_results_seen_pages_stub():
    fmt = PlainTextFormatter()
    result = BrowseResult(
        contexts=[_page_context(7), _page_context(8)],
        reference_code=REF_CODE,
        pages_requested="7-8",
    )
    out = fmt.format_browse_results(result, seen_page_numbers={7})

    assert "📖 Pages loaded: 2 (1 new, 1 previously shown)" in out
    assert "📄 Page 7 (previously shown in this session)" in out
    # Page 8 is new -> shown in full with its links
    assert "📄 Page 8" in out
    assert "📝 ALTO XML:" in out


def test_format_browse_results_with_oai_metadata():
    fmt = PlainTextFormatter()
    metadata = OAIPMHMetadata(
        identifier=REF_CODE,
        title="Domböcker Stockholms rådhusrätt",
        unitdate="1734-1735",
        repository="Stockholms stadsarkiv",
        unitid="SE/SSA/0145",
        description="Protokoll och domar från rådhusrätten.",
        nad_link="https://sok.riksarkivet.se/nad/12345",
    )
    result = BrowseResult(
        contexts=[_page_context(7)],
        reference_code=REF_CODE,
        pages_requested="7",
        oai_metadata=metadata,
    )
    out = fmt.format_browse_results(result)

    assert "📋 Title: Domböcker Stockholms rådhusrätt" in out
    assert "📅 Date Range: 1734-1735" in out
    assert "🏛️  Repository: Stockholms stadsarkiv" in out
    assert "🔖 Unit ID: SE/SSA/0145" in out
    assert "📝 Protokoll och domar från rådhusrätten." in out
    assert "🔗 NAD Link: https://sok.riksarkivet.se/nad/12345" in out


def test_format_browse_results_non_digitised_metadata_only():
    fmt = PlainTextFormatter()
    metadata = OAIPMHMetadata(
        identifier=REF_CODE,
        title="Ej digitaliserat material",
        unitdate="1600-1650",
        repository="Riksarkivet",
        description="Endast metadata tillgänglig.",
        nad_link="https://sok.riksarkivet.se/nad/999",
        iiif_manifest="https://lbiiif.riksarkivet.se/arkis!R0002497/manifest",
    )
    # No page contexts + metadata present -> non-digitised branch.
    result = BrowseResult(contexts=[], reference_code=REF_CODE, pages_requested="1-5", oai_metadata=metadata)
    out = fmt.format_browse_results(result)

    assert "⚠️ This material is not digitised or transcribed" in out
    assert f"📄 Reference Code: {REF_CODE}" in out
    assert "📋 Title: Ej digitaliserat material" in out
    assert "📅 Date Range: 1600-1650" in out
    assert "🏛️  Repository: Riksarkivet" in out
    assert "📝 Description: Endast metadata tillgänglig." in out
    assert "🔗 View Online: https://sok.riksarkivet.se/nad/999" in out
    # IIIF manifest converted to a bildvisaren viewer URL.
    assert "🖼️  View Images: https://sok.riksarkivet.se/bildvisning/R0002497" in out
    # Should NOT fall through to the page-context rendering.
    assert "📄 Page" not in out


def test_format_browse_results_digitised_but_pages_not_found():
    # manifest_id set (digitised) + no contexts = the requested page(s) don't
    # exist — must not claim the material isn't digitised (issue #118).
    fmt = PlainTextFormatter()
    metadata = OAIPMHMetadata(identifier=REF_CODE, title="Digitised volume", repository="Riksarkivet")
    result = BrowseResult(contexts=[], reference_code=REF_CODE, pages_requested="999", manifest_id="R0002497", oai_metadata=metadata)
    out = fmt.format_browse_results(result)

    assert "No pages found for the requested page(s) '999'" in out
    assert "IS digitised" in out
    assert "not digitised or transcribed" not in out


def test_format_browse_results_non_digitised_skips_placeholder_title():
    fmt = PlainTextFormatter()
    # "(No title)" placeholder should be suppressed.
    metadata = OAIPMHMetadata(identifier=REF_CODE, title="(No title)")
    result = BrowseResult(contexts=[], reference_code=REF_CODE, pages_requested="1", oai_metadata=metadata)
    out = fmt.format_browse_results(result)
    assert "⚠️ This material is not digitised" in out
    assert "📋 Title:" not in out

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
    DocumentLinks,
    GenericReference,
    Metadata,
    PageInfo,
    RecordsResponse,
    SearchRecord,
    SearchResult,
    Snippet,
    TranscribedText,
)


# ---------------------------------------------------------------------------
# Factories for realistic sample records
# ---------------------------------------------------------------------------

REF_CODE = "SE/RA/310187/1"
MANIFEST_ID = "R0001203"


def _snippet_record(
    *,
    ref_code: str = REF_CODE,
    caption: str | None = "Dombok 1734",
    date: str | None = "1734",
    institution: str | None = "Riksarkivet",
    num_total: int = 2,
    snippets: list[Snippet] | None = None,
) -> SearchRecord:
    """A transcribed record that carries text snippets (search-hit style)."""
    if snippets is None:
        snippets = [
            Snippet(text="Anna reste till Stockholm", pages=[PageInfo(id=f"{MANIFEST_ID}_00007")]),
            Snippet(text="handel i Stockholm stad", pages=[PageInfo(id=f"{MANIFEST_ID}_00052")]),
        ]
    archival = [GenericReference(caption=institution)] if institution is not None else None
    return SearchRecord(
        id=MANIFEST_ID,
        objectType="Record",
        type="Volume",
        caption=caption,
        metadata=Metadata(
            referenceCode=ref_code,
            date=date,
            archivalInstitution=archival,
        ),
        transcribedText=TranscribedText(numTotal=num_total, snippets=snippets),
    )


def _metadata_record(
    *,
    ref_code: str = REF_CODE,
    caption: str | None = "Länsräkenskaper",
    object_type: str = "Record",
    type_: str | None = "Volume",
    hierarchy: list[GenericReference] | None = None,
    provenance: list[GenericReference] | None = None,
    links: DocumentLinks | None = None,
) -> SearchRecord:
    """A metadata-only record (no transcribed snippets)."""
    return SearchRecord(
        id="R0009999",
        objectType=object_type,
        type=type_,
        caption=caption,
        metadata=Metadata(
            referenceCode=ref_code,
            hierarchy=hierarchy,
            provenance=provenance,
        ),
        transcribedText=None,
        _links=links,
    )


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
# format_text
# ---------------------------------------------------------------------------


def test_format_text_returns_content_unchanged():
    fmt = PlainTextFormatter()
    assert fmt.format_text("hello world") == "hello world"


def test_format_text_ignores_style_name():
    fmt = PlainTextFormatter()
    assert fmt.format_text("plain", style_name="bold red") == "plain"


# ---------------------------------------------------------------------------
# format_table
# ---------------------------------------------------------------------------


def test_format_table_single_row_aligns_columns():
    fmt = PlainTextFormatter()
    out = fmt.format_table(["Page", "Hits"], [["7", "3"]])
    lines = out.splitlines()
    assert lines[0].startswith("Page")
    assert "|" in lines[0]
    # separator line of dashes below the header
    assert set(lines[1]) == {"-"}
    assert "7" in lines[2] and "3" in lines[2]


def test_format_table_multiple_rows():
    fmt = PlainTextFormatter()
    out = fmt.format_table(["A", "B"], [["1", "2"], ["3", "4"]])
    assert "1" in out and "4" in out
    # header + separator + 2 data rows
    assert len(out.splitlines()) == 4


def test_format_table_with_title_prepends_title_and_blank_line():
    fmt = PlainTextFormatter()
    out = fmt.format_table(["Col"], [["v"]], table_title="My Table")
    lines = out.splitlines()
    assert lines[0] == "My Table"
    assert lines[1] == ""


# ---------------------------------------------------------------------------
# format_panel
# ---------------------------------------------------------------------------


def test_format_panel_content_only():
    fmt = PlainTextFormatter()
    assert fmt.format_panel("body text") == "body text"


def test_format_panel_with_title():
    fmt = PlainTextFormatter()
    out = fmt.format_panel("body", panel_title="Header")
    assert out == "Header\n\nbody"


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
# format_search_results
# ---------------------------------------------------------------------------


def test_format_search_results_empty_delegates_to_no_results():
    fmt = PlainTextFormatter()
    result = _search_result([], keyword="ghost", offset=0)
    out = fmt.format_search_results(result)
    assert "No results found for 'ghost'" in out


def test_format_search_results_single_record_with_snippets():
    fmt = PlainTextFormatter()
    result = _search_result([_snippet_record()])
    out = fmt.format_search_results(result)

    # header line: 2 snippets across 1 volume
    assert "Found 2 page-level hits across 1 volumes" in out
    assert "📚 Document: SE/RA/310187/1" in out
    assert "🏛️  Institution: Riksarkivet" in out
    assert "📅 Date: 1734" in out
    assert "📄 Title: Dombok 1734" in out
    # page numbers derived from page ids (00007 -> 7, 00052 -> 52)
    assert "📖 Pages with hits: 7, 52" in out
    # num_total == snippet count (2) -> "found", not "shown"
    assert "💡 2 hits found" in out
    # snippet keyword highlighted, using the raw page id
    assert f"Page {MANIFEST_ID}_00007: Anna reste till **Stockholm**" in out


def test_format_search_results_multiple_records():
    fmt = PlainTextFormatter()
    rec_a = _snippet_record(ref_code="SE/RA/111/1", caption="Volym A")
    rec_b = _snippet_record(ref_code="SE/RA/222/2", caption="Volym B")
    result = _search_result([rec_a, rec_b])
    out = fmt.format_search_results(result)

    assert "across 2 volumes" in out
    assert "📚 Document: SE/RA/111/1" in out
    assert "📚 Document: SE/RA/222/2" in out


def test_format_search_results_hit_singular_and_shown_total():
    fmt = PlainTextFormatter()
    # One displayed snippet but num_total=5 -> "1 hit shown (5 total)"
    one = [Snippet(text="Stockholm nämns", pages=[PageInfo(id=f"{MANIFEST_ID}_00003")])]
    result = _search_result([_snippet_record(num_total=5, snippets=one)])
    out = fmt.format_search_results(result)
    assert "💡 1 hit shown (5 total)" in out


def test_format_search_results_more_than_three_snippets_truncated():
    fmt = PlainTextFormatter()
    snippets = [Snippet(text=f"Stockholm rad {i}", pages=[PageInfo(id=f"{MANIFEST_ID}_{i:05d}")]) for i in range(1, 6)]
    result = _search_result([_snippet_record(num_total=5, snippets=snippets)])
    out = fmt.format_search_results(result)
    # Only 3 snippet lines shown, remaining summarised
    assert "...and 2 more pages with hits" in out


def test_format_search_results_metadata_only():
    fmt = PlainTextFormatter()
    rec = _metadata_record(
        hierarchy=[
            GenericReference(caption="Nationell arkivdatabas"),
            GenericReference(caption="Länsstyrelsen"),
        ],
        provenance=[GenericReference(caption="Länsstyrelsen i Stockholm", date="1650-1700")],
        links=DocumentLinks(html="https://sok.riksarkivet.se/html", image=["https://lbiiif.riksarkivet.se/manifest"]),
    )
    result = _search_result([rec])
    out = fmt.format_search_results(result)

    assert "Found 1 volumes matching metadata" in out
    assert "🏷️  Type: Record / Volume" in out
    assert "📂 Context: Nationell arkivdatabas → Länsstyrelsen" in out
    assert "👤 Creator: Länsstyrelsen i Stockholm (1650-1700)" in out
    assert "🔗 View: https://sok.riksarkivet.se/html" in out
    assert "🖼️  IIIF: https://lbiiif.riksarkivet.se/manifest" in out


def test_format_search_results_metadata_only_type_without_subtype():
    fmt = PlainTextFormatter()
    rec = _metadata_record(type_=None)
    result = _search_result([rec])
    out = fmt.format_search_results(result)
    assert "🏷️  Type: Record" in out
    assert "🏷️  Type: Record /" not in out


def test_format_search_results_missing_optional_fields():
    fmt = PlainTextFormatter()
    # No institution, no date, no caption (title falls back to "(No title)").
    rec = _snippet_record(caption=None, date=None, institution=None)
    result = _search_result([rec])
    out = fmt.format_search_results(result)

    assert "📄 Title: (No title)" in out
    assert "🏛️" not in out  # institution line omitted
    assert "📅 Date:" not in out  # date line omitted


def test_format_search_results_long_title_truncated():
    fmt = PlainTextFormatter()
    long_title = "A" * 150
    rec = _snippet_record(caption=long_title)
    result = _search_result([rec])
    out = fmt.format_search_results(result)
    assert "📄 Title: " + "A" * 100 + "..." in out


def test_format_search_results_document_count_capped_display():
    fmt = PlainTextFormatter()
    # limit equals number of records -> display shows "N+"
    recs = [_snippet_record(ref_code=f"SE/RA/{i}/1") for i in range(2)]
    result = _search_result(recs, limit=2)
    out = fmt.format_search_results(result)
    assert "across 2+ volumes" in out


def test_format_search_results_respects_max_documents_to_display():
    fmt = PlainTextFormatter()
    recs = [_snippet_record(ref_code=f"SE/RA/{i}/1") for i in range(5)]
    result = _search_result(recs, limit=20)
    out = fmt.format_search_results(result, maximum_documents_to_display=2)
    assert "... and 3 more documents" in out


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


def test_format_browse_results_non_digitised_skips_placeholder_title():
    fmt = PlainTextFormatter()
    # "(No title)" placeholder should be suppressed.
    metadata = OAIPMHMetadata(identifier=REF_CODE, title="(No title)")
    result = BrowseResult(contexts=[], reference_code=REF_CODE, pages_requested="1", oai_metadata=metadata)
    out = fmt.format_browse_results(result)
    assert "⚠️ This material is not digitised" in out
    assert "📋 Title:" not in out

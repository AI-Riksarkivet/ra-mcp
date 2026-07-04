"""Tests for the PlainTextFormatter in ra-mcp-search-mcp.

The formatter is a set of pure, synchronous functions that turn search/browse
records into plain-text markdown for LLM consumption. These tests build realistic
SearchResult/SearchRecord pydantic models (from ra_mcp_search_lib.models) and
duck-typed browse objects, then assert on concrete substrings in the output.
"""

from types import SimpleNamespace

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
from ra_mcp_search_mcp.formatter import PlainTextFormatter


# --------------------------------------------------------------------------- #
# Factories
# --------------------------------------------------------------------------- #


def _snippet(text: str, page_ids: list[str], score: float = 0.9) -> Snippet:
    return Snippet(text=text, score=score, pages=[PageInfo(id=pid) for pid in page_ids])


def _record(
    ref_code: str = "SE/RA/TEST/1",
    caption: str | None = "Test Volume",
    num_total: int = 3,
    snippets: list[Snippet] | None = None,
    transcribed: bool = True,
    date: str | None = "1669",
    institution: str | None = "Riksarkivet",
    object_type: str = "Record",
    type_: str | None = "Volume",
    hierarchy: list[GenericReference] | None = None,
    provenance: list[GenericReference] | None = None,
    links: DocumentLinks | None = None,
) -> SearchRecord:
    if snippets is None and transcribed:
        snippets = [_snippet("en trolldom sak", ["_00005"])]

    metadata = Metadata(
        referenceCode=ref_code,
        date=date,
        archivalInstitution=[GenericReference(caption=institution)] if institution else None,
        hierarchy=hierarchy,
        provenance=provenance,
    )
    transcribed_text = TranscribedText(numTotal=num_total, snippets=snippets or []) if transcribed else None

    return SearchRecord(
        id=ref_code,
        objectType=object_type,
        type=type_,
        caption=caption,
        metadata=metadata,
        transcribedText=transcribed_text,
        _links=links,
    )


def _result(
    records: list[SearchRecord],
    keyword: str = "trolldom",
    limit: int = 20,
    offset: int = 0,
    total_hits: int = 42,
) -> SearchResult:
    response = RecordsResponse(
        totalHits=total_hits,
        items=records,
        hits=len(records),
        offset=offset,
    )
    return SearchResult(response=response, transcribed_text=keyword, limit=limit, offset=offset)


def _fmt() -> PlainTextFormatter:
    return PlainTextFormatter()


# --------------------------------------------------------------------------- #
# format_text
# --------------------------------------------------------------------------- #


def test_format_text_returns_content_unchanged():
    out = _fmt().format_text("hello **world**", style_name="bold")
    assert out == "hello **world**"


def test_format_text_empty_string():
    assert _fmt().format_text("") == ""


# --------------------------------------------------------------------------- #
# format_table
# --------------------------------------------------------------------------- #


def test_format_table_aligns_columns_and_adds_separator():
    out = _fmt().format_table(["Name", "N"], [["Stockholm", "1"], ["Mora", "42"]])
    lines = out.splitlines()
    # header pads the short column so values line up under it
    assert lines[0] == "Name      | N "
    # a dedicated separator line made entirely of dashes
    assert any(line and set(line) == {"-"} for line in lines)
    assert "Stockholm" in out
    assert "Mora" in out


def test_format_table_with_title():
    out = _fmt().format_table(["A"], [["1"]], table_title="My Table")
    assert out.startswith("My Table\n")
    assert "A" in out
    assert "1" in out


def test_format_table_single_row():
    out = _fmt().format_table(["Col"], [["only"]])
    assert "Col" in out
    assert "only" in out


# --------------------------------------------------------------------------- #
# format_panel
# --------------------------------------------------------------------------- #


def test_format_panel_with_title_has_blank_line_between():
    out = _fmt().format_panel("body text", panel_title="Heading")
    assert out == "Heading\n\nbody text"


def test_format_panel_without_title_is_just_content():
    out = _fmt().format_panel("body text")
    assert out == "body text"


# --------------------------------------------------------------------------- #
# highlight_search_keyword
# --------------------------------------------------------------------------- #


def test_highlight_search_keyword_wraps_match_in_bold():
    out = _fmt().highlight_search_keyword("the trolldom case", "trolldom")
    assert out == "the **trolldom** case"


def test_highlight_search_keyword_passthrough_when_already_marked():
    # API text already containing **markers** is returned untouched
    out = _fmt().highlight_search_keyword("a **word** b", "word")
    assert out == "a **word** b"


def test_highlight_search_keyword_empty_keyword_returns_input():
    out = _fmt().highlight_search_keyword("plain text", "")
    assert out == "plain text"


# --------------------------------------------------------------------------- #
# format_error_message
# --------------------------------------------------------------------------- #


def test_format_error_message_with_suggestions():
    out = _fmt().format_error_message("bad query", ["use quotes", "try again"])
    assert "**Error**: bad query" in out
    assert "Suggestions" in out
    assert "- use quotes" in out
    assert "- try again" in out


def test_format_error_message_without_suggestions():
    out = _fmt().format_error_message("boom")
    assert "**Error**: boom" in out
    assert "Suggestions" not in out


# --------------------------------------------------------------------------- #
# format_no_results_message
# --------------------------------------------------------------------------- #


def test_format_no_results_message_at_offset_zero():
    out = _fmt().format_no_results_message(_result([], keyword="häxa", offset=0))
    assert "No results found for 'häxa'" in out
    assert "make sure to use" in out


def test_format_no_results_message_at_higher_offset():
    out = _fmt().format_no_results_message(_result([], keyword="häxa", offset=20, total_hits=5))
    assert "No more results found for 'häxa' at offset 20" in out
    assert "Total results: 5" in out


# --------------------------------------------------------------------------- #
# format_search_results — empty
# --------------------------------------------------------------------------- #


def test_format_search_results_empty_falls_back_to_no_results():
    fmt = _fmt()
    out = fmt.format_search_results(_result([], keyword="nothing", offset=0))
    assert "No results found for 'nothing'" in out
    assert fmt.items_scanned == 0


# --------------------------------------------------------------------------- #
# format_search_results — transcribed (with snippets)
# --------------------------------------------------------------------------- #


def test_format_search_results_single_transcribed_record():
    rec = _record(ref_code="SE/RA/310187/1", caption="Dombok", num_total=1, snippets=[_snippet("en trolldom sak", ["_00066"])])
    out = _fmt().format_search_results(_result([rec], keyword="trolldom"))
    assert "Found 1 page-level hits across 1 volumes" in out
    assert "📚 Document: SE/RA/310187/1" in out
    assert "🏛️  Institution: Riksarkivet" in out
    assert "📅 Date: 1669" in out
    assert "📄 Title: Dombok" in out
    # pages line uses numeric page ids, snippet line uses the raw id
    assert "📖 Pages with hits: 66" in out
    assert "💡 1 hit found" in out
    assert "Page _00066: en **trolldom** sak" in out
    assert "Tip: Use browse_document" in out


def test_format_search_results_hits_shown_vs_total_label():
    # num_total (10) exceeds the number of snippets returned (2) -> "shown (N total)"
    snippets = [_snippet("trolldom one", ["_00001"]), _snippet("trolldom two", ["_00002"])]
    rec = _record(num_total=10, snippets=snippets)
    out = _fmt().format_search_results(_result([rec], keyword="trolldom"))
    assert "💡 2 hits shown (10 total)" in out


def test_format_search_results_truncates_snippets_beyond_three():
    snippets = [_snippet(f"trolldom {n}", [f"_{n:05d}"]) for n in range(1, 6)]
    rec = _record(num_total=5, snippets=snippets)
    out = _fmt().format_search_results(_result([rec], keyword="trolldom"))
    assert "...and 2 more pages with hits" in out
    # only the first three snippet lines are rendered
    assert "Page _00003: " in out
    assert "Page _00004: " not in out


def test_format_search_results_multiple_records_and_snippet_count_summary():
    recs = [
        _record(ref_code="SE/RA/A", snippets=[_snippet("trolldom a", ["_00001"])], num_total=1),
        _record(ref_code="SE/RA/B", snippets=[_snippet("trolldom b", ["_00002"])], num_total=1),
    ]
    out = _fmt().format_search_results(_result(recs, keyword="trolldom"))
    assert "Found 2 page-level hits across 2 volumes" in out
    assert "📚 Document: SE/RA/A" in out
    assert "📚 Document: SE/RA/B" in out


def test_format_search_results_shows_plus_when_at_limit():
    recs = [
        _record(ref_code="SE/RA/A", snippets=[_snippet("trolldom a", ["_00001"])], num_total=1),
        _record(ref_code="SE/RA/B", snippets=[_snippet("trolldom b", ["_00002"])], num_total=1),
    ]
    out = _fmt().format_search_results(_result(recs, keyword="trolldom", limit=2))
    assert "across 2+ volumes" in out


def test_format_search_results_respects_max_documents_and_reports_remaining():
    recs = [_record(ref_code=f"SE/RA/{n}", snippets=[_snippet(f"trolldom {n}", [f"_{n:05d}"])], num_total=1) for n in range(1, 4)]
    fmt = _fmt()
    out = fmt.format_search_results(_result(recs, keyword="trolldom"), maximum_documents_to_display=1)
    assert "📚 Document: SE/RA/1" in out
    assert "📚 Document: SE/RA/2" not in out
    assert "... and 2 more documents" in out
    assert fmt.items_scanned == 1


def test_format_search_results_snippet_without_pages_does_not_crash():
    rec = _record(num_total=1, snippets=[_snippet("trolldom no page", [])])
    out = _fmt().format_search_results(_result([rec], keyword="trolldom"))
    # no page-specific line is emitted, but the document still renders
    assert "📚 Document: SE/RA/TEST/1" in out
    assert "Page _" not in out


# --------------------------------------------------------------------------- #
# format_search_results — missing / None optional fields
# --------------------------------------------------------------------------- #


def test_format_search_results_missing_optional_fields():
    rec = _record(
        ref_code="SE/RA/MIN/1",
        caption=None,  # -> "(No title)"
        institution=None,  # no institution line
        date=None,  # no date line
        snippets=[_snippet("trolldom min", ["_00007"])],
        num_total=1,
    )
    out = _fmt().format_search_results(_result([rec], keyword="trolldom"))
    assert "📄 Title: (No title)" in out
    assert "Institution:" not in out
    assert "📅 Date:" not in out


def test_format_search_results_long_title_is_truncated():
    long_title = "A" * 150
    rec = _record(caption=long_title, snippets=[_snippet("trolldom x", ["_00001"])], num_total=1)
    out = _fmt().format_search_results(_result([rec], keyword="trolldom"))
    assert "A" * 100 + "..." in out
    assert "A" * 150 not in out


# --------------------------------------------------------------------------- #
# format_search_results — metadata-only (no snippets)
# --------------------------------------------------------------------------- #


def test_format_search_results_metadata_only_document():
    rec = _record(
        ref_code="SE/RA/META/1",
        caption="Some Archive",
        transcribed=False,
        object_type="Record",
        type_="Volume",
        hierarchy=[GenericReference(caption="Riksarkivet"), GenericReference(caption="Länsstyrelsen")],
        provenance=[GenericReference(caption="Mora tingslag", date="1669")],
        links=DocumentLinks(
            html="https://sok.riksarkivet.se/x",
            image=["https://lbiiif.riksarkivet.se/arkis!R0002497/manifest"],
        ),
    )
    out = _fmt().format_search_results(_result([rec], keyword="Stockholm"))
    assert "Found 1 volumes matching metadata" in out
    assert "🏷️  Type: Record / Volume" in out
    assert "📂 Context: Riksarkivet → Länsstyrelsen" in out
    assert "👤 Creator: Mora tingslag (1669)" in out
    assert "🔗 View: https://sok.riksarkivet.se/x" in out
    # IIIF manifest is converted to a bildvisning viewer URL
    assert "🖼️  View Images: https://sok.riksarkivet.se/bildvisning/R0002497" in out


def test_format_search_results_metadata_only_falls_back_to_raw_iiif():
    # image URL that is not a convertible arkis!<id>/manifest keeps the raw IIIF link
    rec = _record(
        ref_code="SE/RA/META/2",
        transcribed=False,
        links=DocumentLinks(image=["https://lbiiif.riksarkivet.se/collection/arkiv"]),
    )
    out = _fmt().format_search_results(_result([rec], keyword="Stockholm"))
    assert "🖼️  IIIF: https://lbiiif.riksarkivet.se/collection/arkiv" in out
    assert "View Images:" not in out


# --------------------------------------------------------------------------- #
# format_search_results — seen_pages deduplication
# --------------------------------------------------------------------------- #


def test_format_search_results_skips_fully_seen_document():
    rec = _record(ref_code="SE/RA/DUP", snippets=[_snippet("trolldom", ["_00005"])], num_total=1)
    out = _fmt().format_search_results(
        _result([rec], keyword="trolldom"),
        seen_pages={"SE/RA/DUP": [5]},
    )
    assert "(1 previously shown document(s) omitted)" in out
    assert "Page _00005:" not in out


def test_format_search_results_shows_only_new_pages_for_seen_document():
    snippets = [_snippet("trolldom old", ["_00005"]), _snippet("trolldom new", ["_00010"])]
    rec = _record(ref_code="SE/RA/DUP2", snippets=snippets, num_total=2)
    out = _fmt().format_search_results(
        _result([rec], keyword="trolldom"),
        seen_pages={"SE/RA/DUP2": [5]},
    )
    assert "📚 Document: SE/RA/DUP2 (previously shown — new pages only)" in out
    assert "📖 New pages: 10" in out
    assert "Page _00010: **trolldom** new" in out


# --------------------------------------------------------------------------- #
# format_browse_results
# --------------------------------------------------------------------------- #


def _page_context(
    page_number: int = 7,
    page_id: str = "_00007",
    full_text: str = "handwritten transcription text",
    alto_url: str = "https://sok.riksarkivet.se/dokument/alto/x_00007",
    image_url: str = "https://lbiiif.riksarkivet.se/image/x/full/max/0/default.jpg",
    bildvisning_url: str = "https://sok.riksarkivet.se/bildvisning/x_00007",
) -> SimpleNamespace:
    return SimpleNamespace(
        page_number=page_number,
        page_id=page_id,
        full_text=full_text,
        alto_url=alto_url,
        image_url=image_url,
        bildvisning_url=bildvisning_url,
    )


def _browse_result(
    contexts: list[SimpleNamespace],
    reference_code: str = "SE/RA/310187/1",
    oai_metadata: SimpleNamespace | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        contexts=contexts,
        reference_code=reference_code,
        oai_metadata=oai_metadata,
    )


def test_format_browse_results_no_contexts():
    out = _fmt().format_browse_results(_browse_result([], reference_code="SE/RA/EMPTY"))
    assert out == "No page contexts found for SE/RA/EMPTY"


def test_format_browse_results_single_page_minimal():
    out = _fmt().format_browse_results(_browse_result([_page_context(page_number=7)]))
    assert "📚 Document: SE/RA/310187/1" in out
    assert "📖 Pages loaded: 1" in out
    assert "📄 Page 7" in out
    assert "handwritten transcription text" in out
    assert "📝 ALTO XML: https://sok.riksarkivet.se/dokument/alto/x_00007" in out
    assert "🖼️  Image:" in out
    assert "👁️  Bildvisning:" in out


def test_format_browse_results_highlights_term_in_text():
    ctx = _page_context(full_text="a mention of Stockholm here")
    out = _fmt().format_browse_results(_browse_result([ctx]), highlight_term="Stockholm")
    assert "a mention of **Stockholm** here" in out


def test_format_browse_results_with_oai_metadata():
    oai = SimpleNamespace(
        title="Domboksprotokoll",
        repository="Landsarkivet i Uppsala",
        unitid="SE/RA/OTHER/9",
        nad_link="https://sok.riksarkivet.se/nad/12345",
    )
    out = _fmt().format_browse_results(_browse_result([_page_context()], reference_code="SE/RA/310187/1", oai_metadata=oai))
    assert "📋 Title: Domboksprotokoll" in out
    assert "🏛️  Repository: Landsarkivet i Uppsala" in out
    assert "🔖 Unit ID: SE/RA/OTHER/9" in out
    assert "🔗 NAD Link: https://sok.riksarkivet.se/nad/12345" in out


def test_format_browse_results_omits_empty_oai_and_missing_image_links():
    # "(No title)" title and a unitid equal to the reference_code are both suppressed;
    # a page with no image/bildvisning URL only shows the ALTO link.
    oai = SimpleNamespace(
        title="(No title)",
        repository="",
        unitid="SE/RA/310187/1",
        nad_link="",
    )
    ctx = _page_context(image_url="", bildvisning_url="")
    out = _fmt().format_browse_results(_browse_result([ctx], reference_code="SE/RA/310187/1", oai_metadata=oai))
    assert "📋 Title:" not in out
    assert "🔖 Unit ID:" not in out
    assert "🏛️  Repository:" not in out
    assert "📝 ALTO XML:" in out
    assert "🖼️  Image:" not in out
    assert "👁️  Bildvisning:" not in out

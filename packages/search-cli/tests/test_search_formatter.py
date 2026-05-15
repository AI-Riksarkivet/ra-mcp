"""Tests for search-cli RichConsoleFormatter."""

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

from ra_mcp_search_cli.formatter import RichConsoleFormatter


def _make_formatter() -> RichConsoleFormatter:
    return RichConsoleFormatter(Console(force_terminal=True, width=120))


def _make_record(
    record_id: str = "SE/RA/TEST/1",
    ref_code: str = "SE/RA/TEST/1",
    caption: str = "Test Record",
    num_snippets: int = 2,
    num_total: int = 5,
    institution: str = "Riksarkivet",
    date: str | None = "1700-1800",
    keyword: str = "trolldom",
    object_type: str = "Record",
    record_type: str | None = "Volume",
    hierarchy: list[GenericReference] | None = None,
    provenance: list[GenericReference] | None = None,
    note: str | None = None,
    links: DocumentLinks | None = None,
) -> SearchRecord:
    snippets = [
        Snippet(
            text=f"snippet {j} with {keyword}",
            score=0.9 - j * 0.1,
            pages=[PageInfo(id=f"_{j:05d}")],
        )
        for j in range(1, num_snippets + 1)
    ]
    return SearchRecord(
        id=record_id,
        objectType=object_type,
        type=record_type,
        caption=caption,
        metadata=Metadata(
            referenceCode=ref_code,
            date=date,
            archivalInstitution=[GenericReference(caption=institution)] if institution else None,
            hierarchy=hierarchy,
            provenance=provenance,
            note=note,
        ),
        transcribedText=TranscribedText(numTotal=num_total, snippets=snippets),
        _links=links,
    )


def _make_search_result(
    records: list[SearchRecord] | None = None,
    keyword: str = "trolldom",
    total_hits: int = 10,
    offset: int = 0,
    limit: int = 50,
) -> SearchResult:
    if records is None:
        records = [_make_record(keyword=keyword)]
    response = RecordsResponse(totalHits=total_hits, items=records, hits=len(records), offset=offset)
    return SearchResult(response=response, transcribed_text=keyword, limit=limit, offset=offset)


# ── format_text ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,style,expected",
    [
        pytest.param("hello", "bold", "[bold]hello[/bold]", id="with-style"),
        pytest.param("plain", "", "plain", id="no-style"),
    ],
)
def test_format_text(text, style, expected):
    assert _make_formatter().format_text(text, style) == expected


# ── format_table ─────────────────────────────────────────────────────────


def test_format_table_returns_table():
    table = _make_formatter().format_table(["A", "B"], [["1", "2"]], "Title")
    assert isinstance(table, Table)


# ── format_panel ─────────────────────────────────────────────────────────


def test_format_panel_returns_panel():
    panel = _make_formatter().format_panel("content", "title", "blue")
    assert isinstance(panel, Panel)


def test_format_panel_defaults():
    panel = _make_formatter().format_panel("content")
    assert panel.border_style == "green"


# ── highlight_search_keyword ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,keyword,expected_fragment",
    [
        pytest.param(
            "found **trolldom** here",
            "trolldom",
            "[bold yellow underline]trolldom[/bold yellow underline]",
            id="api-markers-converted",
        ),
        pytest.param(
            "text with Trolldom inside",
            "trolldom",
            "[bold yellow underline]Trolldom[/bold yellow underline]",
            id="keyword-case-insensitive",
        ),
        pytest.param(
            "nothing to see",
            "",
            "nothing to see",
            id="empty-keyword-unchanged",
        ),
        pytest.param(
            "no match here",
            "xyz",
            "no match here",
            id="keyword-not-found",
        ),
    ],
)
def test_highlight_search_keyword(text, keyword, expected_fragment):
    result = _make_formatter().highlight_search_keyword(text, keyword)
    assert expected_fragment in result


def test_highlight_api_markers_take_precedence_over_keyword():
    result = _make_formatter().highlight_search_keyword("**word** and more", "more")
    assert "[bold yellow underline]word[/bold yellow underline]" in result
    assert "[bold yellow underline]more[/bold yellow underline]" not in result


# ── _build_institution_column ────────────────────────────────────────────


def test_institution_column_with_institution():
    fmt = _make_formatter()
    doc = _make_record(institution="Riksarkivet")
    col = fmt._build_institution_column(doc)
    assert "Riksarkivet" in col


def test_institution_column_without_institution():
    fmt = _make_formatter()
    doc = _make_record(institution="")
    col = fmt._build_institution_column(doc)
    assert "SE/RA/TEST/1" in col


def test_institution_column_shows_total_hits():
    fmt = _make_formatter()
    doc = _make_record(num_snippets=2, num_total=10)
    col = fmt._build_institution_column(doc)
    assert "2 hits shown (10 total)" in col


def test_institution_column_exact_hits():
    fmt = _make_formatter()
    doc = _make_record(num_snippets=3, num_total=3)
    col = fmt._build_institution_column(doc)
    assert "3 hits found" in col


def test_institution_column_single_hit():
    fmt = _make_formatter()
    doc = _make_record(num_snippets=1, num_total=1)
    col = fmt._build_institution_column(doc)
    assert "1 hit found" in col


def test_institution_column_with_date():
    fmt = _make_formatter()
    doc = _make_record(date="1750")
    col = fmt._build_institution_column(doc)
    assert "1750" in col


def test_institution_column_no_date():
    fmt = _make_formatter()
    doc = _make_record(date=None)
    col = fmt._build_institution_column(doc)
    assert "📅" not in col


def test_institution_column_metadata_match():
    doc = SearchRecord(
        id="SE/RA/1",
        objectType="Record",
        metadata=Metadata(referenceCode="SE/RA/1"),
    )
    col = _make_formatter()._build_institution_column(doc)
    assert "Metadata match" in col


# ── _build_content_column ────────────────────────────────────────────────


def test_content_column_with_title():
    fmt = _make_formatter()
    doc = _make_record(caption="Important Document")
    col = fmt._build_content_column(doc, "trolldom")
    assert "Important Document" in col


def test_content_column_no_title():
    fmt = _make_formatter()
    doc = _make_record(caption=None)
    col = fmt._build_content_column(doc, "test")
    assert "(No title)" in col


def test_content_column_object_type():
    fmt = _make_formatter()
    doc = _make_record(object_type="Record", record_type="Volume")
    col = fmt._build_content_column(doc, "test")
    assert "Record" in col
    assert "Volume" in col


def test_content_column_with_hierarchy():
    fmt = _make_formatter()
    doc = _make_record(hierarchy=[
        GenericReference(caption="Level 1"),
        GenericReference(caption="Level 2"),
    ])
    col = fmt._build_content_column(doc, "test")
    assert "Level 1" in col


def test_content_column_with_provenance():
    fmt = _make_formatter()
    doc = _make_record(provenance=[GenericReference(caption="Creator", date="1700")])
    col = fmt._build_content_column(doc, "test")
    assert "Creator" in col
    assert "1700" in col


def test_content_column_with_note():
    fmt = _make_formatter()
    doc = _make_record(note="Important note about this document")
    col = fmt._build_content_column(doc, "test")
    assert "Important note" in col


def test_content_column_with_links():
    fmt = _make_formatter()
    doc = _make_record(links=DocumentLinks(html="https://example.com/doc", image=["https://example.com/img"]))
    col = fmt._build_content_column(doc, "test")
    assert "https://example.com/doc" in col
    assert "https://example.com/img" in col


def test_content_column_snippets_capped_at_three():
    fmt = _make_formatter()
    doc = _make_record(num_snippets=5, num_total=5)
    col = fmt._build_content_column(doc, "test")
    assert "2 more pages with hits" in col


def test_content_column_keyword_highlighted():
    fmt = _make_formatter()
    doc = _make_record(keyword="häxa")
    col = fmt._build_content_column(doc, "häxa")
    assert "[bold yellow underline]" in col


# ── format_search_results ───────────────────────────────────────────────


def test_format_search_results_returns_table():
    result = _make_search_result()
    table = _make_formatter().format_search_results(result)
    assert isinstance(table, Table)


def test_format_search_results_empty():
    result = _make_search_result(records=[], total_hits=0)
    msg = _make_formatter().format_search_results(result)
    assert isinstance(msg, str)
    assert "trolldom" in msg


def test_format_search_results_max_display():
    records = [_make_record(record_id=f"SE/RA/{i}", ref_code=f"SE/RA/{i}") for i in range(5)]
    result = _make_search_result(records=records, total_hits=5)
    table = _make_formatter().format_search_results(result, max_display=3)
    assert isinstance(table, Table)
    assert table.row_count == 3


# ── format_search_summary_stats ─────────────────────────────────────────


def test_summary_stats_basic():
    lines = _make_formatter().format_search_summary_stats(
        snippet_count=10, records_count=5, total_hits=5, offset=0
    )
    assert any("10" in line for line in lines)
    assert any("5" in line for line in lines)


def test_summary_stats_with_pagination():
    lines = _make_formatter().format_search_summary_stats(
        snippet_count=20, records_count=10, total_hits=100, offset=50
    )
    assert any("100" in line for line in lines)
    assert any("50" in line for line in lines)


def test_summary_stats_no_extra_line_when_all_shown():
    lines = _make_formatter().format_search_summary_stats(
        snippet_count=3, records_count=3, total_hits=3, offset=0
    )
    assert len(lines) == 1


def test_summary_stats_plus_when_at_max():
    lines = _make_formatter().format_search_summary_stats(
        snippet_count=100, records_count=50, total_hits=200, offset=0, max_requested=50
    )
    assert any("50+" in line for line in lines)


def test_summary_stats_no_plus_when_below_max():
    lines = _make_formatter().format_search_summary_stats(
        snippet_count=10, records_count=5, total_hits=5, offset=0, max_requested=50
    )
    assert not any("+" in line for line in lines)


# ── format_browse_example ────────────────────────────────────────────────


def test_browse_example_with_snippets():
    result = _make_search_result()
    lines = _make_formatter().format_browse_example(result.items, "trolldom")
    assert len(lines) == 2
    assert "ra browse" in lines[1]
    assert "trolldom" in lines[1]


def test_browse_example_empty():
    lines = _make_formatter().format_browse_example([], "test")
    assert lines == []


def test_browse_example_no_snippets():
    doc = SearchRecord(
        id="SE/RA/1",
        objectType="Record",
        metadata=Metadata(referenceCode="SE/RA/1"),
    )
    lines = _make_formatter().format_browse_example([doc], "test")
    assert lines == []


# ── format_remaining_documents ───────────────────────────────────────────


@pytest.mark.parametrize(
    "total,displayed,expect_message",
    [
        pytest.param(30, 20, True, id="more-remaining"),
        pytest.param(10, 20, False, id="all-shown"),
        pytest.param(5, 5, False, id="exact-match"),
    ],
)
def test_format_remaining_documents(total, displayed, expect_message):
    msg = _make_formatter().format_remaining_documents(total, displayed)
    if expect_message:
        assert "10 more" in msg
    else:
        assert msg == ""


# ── format_no_results_message ────────────────────────────────────────────


def test_no_results_at_offset_zero():
    result = _make_search_result(records=[], total_hits=0, offset=0)
    msg = _make_formatter().format_no_results_message(result)
    assert "No results found" in msg


def test_no_results_at_positive_offset():
    result = _make_search_result(records=[], total_hits=50, offset=50)
    msg = _make_formatter().format_no_results_message(result)
    assert "No more results" in msg
    assert "50" in msg

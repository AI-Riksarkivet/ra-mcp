"""Tests for aktiebolag formatter (pure sync markdown/text formatters)."""

from __future__ import annotations

from ra_mcp_aktiebolag_lib.search_operations import SearchResult
from ra_mcp_aktiebolag_mcp.formatter import (
    format_bolag_results,
    format_styrelse_results,
)


# ---------------------------------------------------------------------------
# Helpers: build realistic SearchResult objects with plain-dict records.
# Records mirror the LanceDB .to_list() shape (AktiebolagRecord / StyrelseRecord
# field names) that the formatter reads via rec.get(...).
# ---------------------------------------------------------------------------


def _bolag_record(**overrides) -> dict:
    rec = {
        "bolagets_namn": "Aktiebolaget Svenska Kullagerfabriken",
        "aldre_namn": "SKF",
        "argang": "1907",
        "postadress": "Göteborg",
        "bolagets_andamal": "Tillverkning av kullager",
        "styrelsesate": "Göteborg",
        "verkstall_dir": "Sven Wingquist",
        "aktiekapital": "2500000",
        "styrelsemedlemmar": "Sven Wingquist; Axel Carlander",
    }
    rec.update(overrides)
    return rec


def _styrelse_record(**overrides) -> dict:
    rec = {
        "styrelsemed": "Wingquist",
        "fornamn": "Sven",
        "titel": "Ingenjör",
        "kon": "M",
        "bolagets_namn": "Aktiebolaget Svenska Kullagerfabriken",
    }
    rec.update(overrides)
    return rec


def _result(records: list[dict], *, total_hits=None, keyword="kullager", offset=0, limit=25) -> SearchResult:
    return SearchResult(
        records=records,
        total_hits=len(records) if total_hits is None else total_hits,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# format_bolag_results
# ---------------------------------------------------------------------------


def test_format_bolag_results_empty_offset_zero():
    out = format_bolag_results(_result([], total_hits=0, keyword="trolldom"))
    assert out == "No company results found for 'trolldom'."


def test_format_bolag_results_empty_with_offset_reports_total():
    out = format_bolag_results(_result([], total_hits=42, keyword="trolldom", offset=25))
    assert "No more company results for 'trolldom' at offset 25" in out
    assert "Total found: 42" in out


def test_format_bolag_results_single_record_full_fields():
    out = format_bolag_results(_result([_bolag_record()], keyword="kullager"))
    # header count line
    assert "Company search results for 'kullager': showing 1 of 1 records (offset 0)" in out
    # header combines name + argang
    assert "--- Aktiebolaget Svenska Kullagerfabriken (1907) ---" in out
    assert "Former name: SKF" in out
    assert "Address: Göteborg" in out
    assert "Seat: Göteborg" in out
    assert "Purpose: Tillverkning av kullager" in out
    assert "Director: Sven Wingquist" in out
    assert "Capital: 2500000 kr" in out
    assert "Board: Sven Wingquist; Axel Carlander" in out


def test_format_bolag_results_header_without_argang():
    out = format_bolag_results(_result([_bolag_record(argang="")]))
    assert "--- Aktiebolaget Svenska Kullagerfabriken ---" in out
    assert "(1907)" not in out


def test_format_bolag_results_multiple_records():
    recs = [
        _bolag_record(bolagets_namn="Alfa AB", argang="1901"),
        _bolag_record(bolagets_namn="Beta AB", argang="1902"),
    ]
    out = format_bolag_results(_result(recs, keyword="ab"))
    assert "showing 2 of 2 records" in out
    assert "--- Alfa AB (1901) ---" in out
    assert "--- Beta AB (1902) ---" in out


def test_format_bolag_results_missing_optional_fields_omitted():
    # Only the name key present; every optional field absent.
    out = format_bolag_results(_result([{"bolagets_namn": "Bara Namn AB"}]))
    assert "--- Bara Namn AB ---" in out
    for label in ("Former name:", "Address:", "Seat:", "Purpose:", "Director:", "Capital:", "Board:"):
        assert label not in out


def test_format_bolag_results_missing_name_uses_placeholder():
    # No bolagets_namn key at all -> .get default '?'
    out = format_bolag_results(_result([{"postadress": "Stockholm"}]))
    assert "--- ? ---" in out
    assert "Address: Stockholm" in out


def test_format_bolag_results_purpose_truncated():
    long_purpose = "A" * 250
    out = format_bolag_results(_result([_bolag_record(bolagets_andamal=long_purpose)]))
    assert "Purpose: " + "A" * 197 + "..." in out
    assert "A" * 250 not in out


def test_format_bolag_results_pagination_hint_present():
    out = format_bolag_results(_result([_bolag_record()], total_hits=10, offset=0, limit=2))
    assert "More results available. Use offset=2 to see the next page." in out


def test_format_bolag_results_no_pagination_hint_on_last_page():
    out = format_bolag_results(_result([_bolag_record()], total_hits=2, offset=0, limit=2))
    assert "More results available" not in out


# ---------------------------------------------------------------------------
# format_styrelse_results
# ---------------------------------------------------------------------------


def test_format_styrelse_results_empty_offset_zero():
    out = format_styrelse_results(_result([], total_hits=0, keyword="wingquist"))
    assert out == "No board member results found for 'wingquist'."


def test_format_styrelse_results_empty_with_offset_reports_total():
    out = format_styrelse_results(_result([], total_hits=7, keyword="wingquist", offset=25))
    assert "No more board member results for 'wingquist' at offset 25" in out
    assert "Total found: 7" in out


def test_format_styrelse_results_single_record_full_fields():
    out = format_styrelse_results(_result([_styrelse_record()], keyword="wingquist"))
    assert "Board member search results for 'wingquist': showing 1 of 1 records (offset 0)" in out
    assert "--- Wingquist Sven ---" in out
    assert "Title: Ingenjör" in out
    assert "Gender: M" in out
    assert "Company: Aktiebolaget Svenska Kullagerfabriken" in out


def test_format_styrelse_results_multiple_records():
    recs = [
        _styrelse_record(styrelsemed="Andersson", fornamn="Anna"),
        _styrelse_record(styrelsemed="Bergström", fornamn="Bo"),
    ]
    out = format_styrelse_results(_result(recs, keyword="styrelse"))
    assert "showing 2 of 2 records" in out
    assert "--- Andersson Anna ---" in out
    assert "--- Bergström Bo ---" in out


def test_format_styrelse_results_name_stripped_when_only_surname():
    out = format_styrelse_results(_result([_styrelse_record(styrelsemed="Andersson", fornamn="")]))
    # No trailing space from the missing first name.
    assert "--- Andersson ---" in out


def test_format_styrelse_results_missing_name_uses_placeholder():
    out = format_styrelse_results(_result([_styrelse_record(styrelsemed="", fornamn="")]))
    assert "--- ? ---" in out


def test_format_styrelse_results_missing_optional_fields_omitted():
    out = format_styrelse_results(_result([{"styrelsemed": "Lundberg", "fornamn": "Lars"}]))
    assert "--- Lundberg Lars ---" in out
    for label in ("Title:", "Gender:", "Company:"):
        assert label not in out


def test_format_styrelse_results_pagination_hint_present():
    out = format_styrelse_results(_result([_styrelse_record()], total_hits=10, offset=0, limit=2))
    assert "More results available. Use offset=2 to see the next page." in out


def test_format_styrelse_results_no_pagination_hint_on_last_page():
    out = format_styrelse_results(_result([_styrelse_record()], total_hits=2, offset=0, limit=2))
    assert "More results available" not in out

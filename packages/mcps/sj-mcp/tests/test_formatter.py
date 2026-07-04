"""Tests for the SJ railway records plain-text formatters.

Covers both public formatters (format_juda_results, format_ritningar_results)
across boundaries: empty result sets (with and without pagination offset),
single record, multiple records, missing/None optional fields, truncation of
long notes, and pagination hints. Records are plain dicts (LanceDB rows), so
these are pure sync tests with no mocks or network.
"""

from __future__ import annotations

from ra_mcp_sj_lib.search_operations import SearchResult
from ra_mcp_sj_mcp.formatter import format_juda_results, format_ritningar_results


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _juda_result(
    records: list[dict],
    *,
    total_hits: int | None = None,
    keyword: str = "stationshus",
    offset: int = 0,
    limit: int = 25,
) -> SearchResult:
    return SearchResult(
        records=records,
        total_hits=len(records) if total_hits is None else total_hits,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


def _ritning_result(
    records: list[dict],
    *,
    total_hits: int | None = None,
    keyword: str = "fasadritning",
    offset: int = 0,
    limit: int = 25,
) -> SearchResult:
    return SearchResult(
        records=records,
        total_hits=len(records) if total_hits is None else total_hits,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


def _juda_record(**overrides) -> dict:
    base = {
        "fbidnr": "10001",
        "fbtext": "ÄSPINGEN 1",
        "fblan": "14",
        "fbkom": "1480",
        "fbagrkod2": "Jernhusen",
        "fbanm": "Stationshus med bostäder",
    }
    base.update(overrides)
    return base


def _ritning_record(**overrides) -> dict:
    base = {
        "bnum": "50001",
        "blad": "1",
        "ben1": "GÖTEBORG N HUS 7",
        "ben": "VVSSITPL",
        "ritn": "R-50001",
        "datm": "1920-05-15",
        "form2": "A1",
        "rtyp2": "PLAN",
        "dkod": "GBG",
        "sakg": "SH",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# JUDA: empty result sets
# ---------------------------------------------------------------------------


def test_format_juda_results_empty_offset_zero():
    out = format_juda_results(_juda_result([], total_hits=0, keyword="trolldom", offset=0))
    assert out == "No JUDA results found for 'trolldom'."


def test_format_juda_results_empty_with_offset_shows_total_and_offset():
    out = format_juda_results(_juda_result([], total_hits=42, keyword="trolldom", offset=25))
    assert "No more JUDA results for 'trolldom'" in out
    assert "offset 25" in out
    assert "Total found: 42" in out


# ---------------------------------------------------------------------------
# JUDA: populated result sets
# ---------------------------------------------------------------------------


def test_format_juda_results_single_record_has_header_and_fields():
    out = format_juda_results(_juda_result([_juda_record()], total_hits=1, keyword="stationshus"))
    assert "JUDA search results for 'stationshus'" in out
    assert "showing 1 of 1 records (offset 0)" in out
    assert "--- JUDA 10001 ---" in out
    assert "Property: ÄSPINGEN 1" in out
    assert "County: 14" in out
    assert "Municipality: 1480" in out
    assert "Owner: Jernhusen" in out
    assert "Notes: Stationshus med bostäder" in out


def test_format_juda_results_multiple_records_all_present():
    records = [
        _juda_record(fbidnr="10001", fbtext="ÄSPINGEN 1"),
        _juda_record(fbidnr="10002", fbtext="GÖTEBORG CENTRAL 3"),
        _juda_record(fbidnr="10003", fbtext="STOCKHOLM C 5"),
    ]
    out = format_juda_results(_juda_result(records, total_hits=3))
    assert "showing 3 of 3 records" in out
    assert "--- JUDA 10001 ---" in out
    assert "--- JUDA 10002 ---" in out
    assert "--- JUDA 10003 ---" in out
    assert "Property: GÖTEBORG CENTRAL 3" in out
    assert "Property: STOCKHOLM C 5" in out


def test_format_juda_results_missing_optional_fields_omits_labels_and_uses_placeholder():
    # Only a property text; no id, county, municipality, owner, or notes.
    rec = {"fbtext": "OKÄND FASTIGHET"}
    out = format_juda_results(_juda_result([rec], total_hits=1))
    assert "--- JUDA ? ---" in out
    assert "Property: OKÄND FASTIGHET" in out
    assert "County:" not in out
    assert "Municipality:" not in out
    assert "Owner:" not in out
    assert "Notes:" not in out


def test_format_juda_results_empty_string_fields_are_skipped():
    rec = _juda_record(fbtext="", fblan="", fbkom="", fbagrkod2="", fbanm="")
    out = format_juda_results(_juda_result([rec], total_hits=1))
    assert "--- JUDA 10001 ---" in out
    assert "Property:" not in out
    assert "County:" not in out
    assert "Notes:" not in out


def test_format_juda_results_truncates_long_notes():
    long_note = "START" + ("x" * 300) + "END"
    rec = _juda_record(fbanm=long_note)
    out = format_juda_results(_juda_result([rec], total_hits=1))
    assert "Notes: START" in out
    assert "..." in out
    # The tail must be dropped by the 150-char truncation.
    assert "END" not in out
    assert long_note not in out


def test_format_juda_results_pagination_hint_when_more_available():
    records = [_juda_record(fbidnr="10001"), _juda_record(fbidnr="10002")]
    out = format_juda_results(_juda_result(records, total_hits=10, offset=0, limit=2))
    assert "More results available. Use offset=2" in out


def test_format_juda_results_no_pagination_hint_on_last_page():
    records = [_juda_record(fbidnr="10001"), _juda_record(fbidnr="10002")]
    out = format_juda_results(_juda_result(records, total_hits=2, offset=0, limit=25))
    assert "More results available" not in out


# ---------------------------------------------------------------------------
# Ritningar: empty result sets
# ---------------------------------------------------------------------------


def test_format_ritningar_results_empty_offset_zero():
    out = format_ritningar_results(_ritning_result([], total_hits=0, keyword="fasad", offset=0))
    assert out == "No drawing results found for 'fasad'."


def test_format_ritningar_results_empty_with_offset_shows_total_and_offset():
    out = format_ritningar_results(_ritning_result([], total_hits=17, keyword="fasad", offset=25))
    assert "No more drawing results for 'fasad'" in out
    assert "offset 25" in out
    assert "Total found: 17" in out


# ---------------------------------------------------------------------------
# Ritningar: populated result sets
# ---------------------------------------------------------------------------


def test_format_ritningar_results_single_record_with_blad_in_header():
    out = format_ritningar_results(_ritning_result([_ritning_record()], total_hits=1, keyword="fasadritning"))
    assert "Drawing search results for 'fasadritning'" in out
    assert "showing 1 of 1 records (offset 0)" in out
    assert "--- Ritning 50001/1 ---" in out
    assert "Station: GÖTEBORG N HUS 7" in out
    assert "Description: VVSSITPL" in out
    assert "Drawing: R-50001" in out
    assert "Date: 1920-05-15" in out
    assert "Format: A1" in out
    assert "Type: PLAN" in out
    assert "District: GBG" in out
    assert "Building type: SH" in out


def test_format_ritningar_results_record_without_blad_omits_slash():
    rec = _ritning_record(bnum="50002", blad="")
    out = format_ritningar_results(_ritning_result([rec], total_hits=1))
    assert "--- Ritning 50002 ---" in out
    assert "50002/" not in out


def test_format_ritningar_results_multiple_records():
    records = [
        _ritning_record(bnum="50001", blad="1", ben1="GÖTEBORG N HUS 7"),
        _ritning_record(bnum="50002", blad="2", ben1="STOCKHOLM C"),
        _ritning_record(bnum="60001", blad="1", ben1="KIRUNA STATION"),
    ]
    out = format_ritningar_results(_ritning_result(records, total_hits=3))
    assert "showing 3 of 3 records" in out
    assert "--- Ritning 50001/1 ---" in out
    assert "--- Ritning 50002/2 ---" in out
    assert "--- Ritning 60001/1 ---" in out
    assert "Station: KIRUNA STATION" in out


def test_format_ritningar_results_missing_optional_fields_uses_placeholder():
    # No bnum, no blad, only a station name present.
    rec = {"ben1": "OKÄND STATION"}
    out = format_ritningar_results(_ritning_result([rec], total_hits=1))
    assert "--- Ritning ? ---" in out
    assert "Station: OKÄND STATION" in out
    assert "Description:" not in out
    assert "Drawing:" not in out
    assert "Date:" not in out
    assert "District:" not in out


def test_format_ritningar_results_pagination_hint_when_more_available():
    records = [_ritning_record(bnum="50001"), _ritning_record(bnum="50002")]
    out = format_ritningar_results(_ritning_result(records, total_hits=8, offset=0, limit=2))
    assert "More results available. Use offset=2" in out


def test_format_ritningar_results_no_pagination_hint_on_last_page():
    records = [_ritning_record(bnum="50001")]
    out = format_ritningar_results(_ritning_result(records, total_hits=1, offset=0, limit=25))
    assert "More results available" not in out

"""Tests for the court-mcp plain-text formatters.

The formatters are pure sync functions that turn a ``SearchResult`` (records as
plain dicts) into an LLM-friendly plain-text string, so these tests need no
async, no ``Client``, and no mocks — just construct a ``SearchResult`` and
assert on concrete substrings of the returned text.
"""

from __future__ import annotations

from ra_mcp_court_lib.search_operations import SearchResult
from ra_mcp_court_mcp.formatter import (
    format_domboksregister_results,
    format_medelstad_results,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _domboksregister_record(**overrides) -> dict:
    """A realistic Domboksregister record dict (matches DomboksregisterRecord fields)."""
    rec = {
        "id": 42,
        "roll": "Kärande",
        "titel": "Länsman",
        "fnamn": "Per",
        "enamn": "Persson",
        "socken": "Kinnevald",
        "plats": "Växjö",
        "anteckning": "Note about a debt case brought before the court.",
        "datum": "1650-06-12",
        "arende": "Skuld",
    }
    rec.update(overrides)
    return rec


def _medelstad_record(**overrides) -> dict:
    """A realistic Medelstad record dict (matches MedelstadRecord fields)."""
    rec = {
        "lopnr": 7,
        "norm_fornamn": "Anna",
        "norm_efternamn": "Nilsdotter",
        "norm_titel": "Hustru",
        "norm_forsamling": "Listerby",
        "norm_plats": "Blekinge",
        "ting_dag": "1690-03-15",
        "ting_typ": "Höstting",
        "mal_nr": "12",
        "mal_typ": "Skuld",
        "mal_referat": "A dispute over an unpaid debt between two neighbours.",
    }
    rec.update(overrides)
    return rec


def _result(records: list[dict], *, total_hits=None, keyword="Persson", offset=0, limit=25) -> SearchResult:
    return SearchResult(
        records=records,
        total_hits=len(records) if total_hits is None else total_hits,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# format_domboksregister_results
# ---------------------------------------------------------------------------


def test_domboksregister_empty_at_offset_zero():
    out = format_domboksregister_results(_result([], total_hits=0, keyword="trolldom"))
    assert out == "No Domboksregister results found for 'trolldom'."


def test_domboksregister_empty_past_last_page():
    out = format_domboksregister_results(_result([], total_hits=100, keyword="trolldom", offset=25))
    assert "No more Domboksregister results for 'trolldom' at offset 25" in out
    assert "Total found: 100" in out


def test_domboksregister_single_record_header_and_fields():
    out = format_domboksregister_results(_result([_domboksregister_record()], keyword="Persson"))
    assert "Domboksregister search results for 'Persson': showing 1 of 1 records (offset 0)" in out
    assert "--- Domboksregister 42 ---" in out
    assert "Name: Per Persson" in out
    assert "Title: Länsman" in out
    assert "Role: Kärande" in out
    assert "Parish: Kinnevald" in out
    assert "Place: Växjö" in out
    assert "Date: 1650-06-12" in out
    assert "Case: Skuld" in out
    assert "Note: Note about a debt case brought before the court." in out


def test_domboksregister_multiple_records_all_present():
    records = [
        _domboksregister_record(id=1, fnamn="Anders", enamn="Andersson"),
        _domboksregister_record(id=2, fnamn="Måns", enamn="Bengtsson"),
    ]
    out = format_domboksregister_results(_result(records))
    assert "showing 2 of 2 records" in out
    assert "--- Domboksregister 1 ---" in out
    assert "--- Domboksregister 2 ---" in out
    assert "Name: Anders Andersson" in out
    assert "Name: Måns Bengtsson" in out


def test_domboksregister_missing_optional_fields_omits_labels():
    # A record with only an id — every optional field absent from the dict.
    out = format_domboksregister_results(_result([{"id": 99}]))
    assert "--- Domboksregister 99 ---" in out
    assert "Name:" not in out
    assert "Title:" not in out
    assert "Role:" not in out
    assert "Parish:" not in out
    assert "Place:" not in out
    assert "Date:" not in out
    assert "Case:" not in out
    assert "Note:" not in out


def test_domboksregister_none_valued_fields_do_not_crash():
    rec = {
        "id": 5,
        "fnamn": "Per",
        "enamn": None,
        "titel": None,
        "roll": None,
        "socken": None,
        "plats": None,
        "datum": None,
        "arende": None,
        "anteckning": None,
    }
    out = format_domboksregister_results(_result([rec]))
    # Only the first name survives; the None enamn is dropped from the join.
    assert "Name: Per" in out
    assert "Title:" not in out
    assert "Note:" not in out


def test_domboksregister_missing_id_uses_placeholder():
    out = format_domboksregister_results(_result([{"fnamn": "Per", "enamn": "Persson"}]))
    assert "--- Domboksregister ? ---" in out


def test_domboksregister_name_uses_first_name_only_when_surname_missing():
    out = format_domboksregister_results(_result([_domboksregister_record(enamn="")]))
    assert "Name: Per" in out
    assert "Name: Per Persson" not in out


def test_domboksregister_long_note_is_truncated_with_ellipsis():
    long_note = "X" * 200
    out = format_domboksregister_results(_result([_domboksregister_record(anteckning=long_note)]))
    assert "..." in out
    assert long_note not in out
    # _truncate keeps max_len-3 chars + "..." for a 150 cap.
    assert "X" * 147 + "..." in out


def test_domboksregister_pagination_hint_when_more_pages():
    out = format_domboksregister_results(_result([_domboksregister_record()], total_hits=100, offset=0, limit=25))
    assert "More results available. Use offset=25 to see the next page." in out


def test_domboksregister_no_pagination_hint_on_last_page():
    out = format_domboksregister_results(_result([_domboksregister_record()], total_hits=1, offset=0, limit=25))
    assert "More results available" not in out


# ---------------------------------------------------------------------------
# format_medelstad_results
# ---------------------------------------------------------------------------


def test_medelstad_empty_at_offset_zero():
    out = format_medelstad_results(_result([], total_hits=0, keyword="häxa"))
    assert out == "No Medelstad results found for 'häxa'."


def test_medelstad_empty_past_last_page():
    out = format_medelstad_results(_result([], total_hits=42, keyword="häxa", offset=25))
    assert "No more Medelstad results for 'häxa' at offset 25" in out
    assert "Total found: 42" in out


def test_medelstad_single_record_header_and_fields():
    out = format_medelstad_results(_result([_medelstad_record()], keyword="Persson"))
    assert "Medelstad search results for 'Persson': showing 1 of 1 records (offset 0)" in out
    assert "--- Medelstad 7 ---" in out
    assert "Name: Anna Nilsdotter" in out
    assert "Title: Hustru" in out
    assert "Parish: Listerby" in out
    assert "Place: Blekinge" in out
    assert "Court: 1690-03-15 (Höstting)" in out
    assert "Case: Skuld nr 12" in out
    assert "Summary: A dispute over an unpaid debt between two neighbours." in out


def test_medelstad_multiple_records_all_present():
    records = [
        _medelstad_record(lopnr=1, norm_fornamn="Nils", norm_efternamn="Månsson"),
        _medelstad_record(lopnr=2, norm_fornamn="Karin", norm_efternamn="Persdotter"),
    ]
    out = format_medelstad_results(_result(records))
    assert "showing 2 of 2 records" in out
    assert "--- Medelstad 1 ---" in out
    assert "--- Medelstad 2 ---" in out
    assert "Name: Nils Månsson" in out
    assert "Name: Karin Persdotter" in out


def test_medelstad_missing_optional_fields_omits_labels():
    out = format_medelstad_results(_result([{"lopnr": 88}]))
    assert "--- Medelstad 88 ---" in out
    assert "Name:" not in out
    assert "Title:" not in out
    assert "Parish:" not in out
    assert "Place:" not in out
    assert "Court:" not in out
    assert "Case:" not in out
    assert "Summary:" not in out


def test_medelstad_missing_lopnr_uses_placeholder():
    out = format_medelstad_results(_result([{"norm_fornamn": "Anna"}]))
    assert "--- Medelstad ? ---" in out


def test_medelstad_court_only_ting_dag_omits_parens():
    out = format_medelstad_results(_result([_medelstad_record(ting_typ="")]))
    assert "Court: 1690-03-15" in out
    assert "(Höstting)" not in out
    assert "1690-03-15 (" not in out


def test_medelstad_court_only_ting_typ():
    out = format_medelstad_results(_result([_medelstad_record(ting_dag="")]))
    assert "Court: Höstting" in out


def test_medelstad_case_only_mal_typ_omits_number():
    out = format_medelstad_results(_result([_medelstad_record(mal_nr="")]))
    assert "Case: Skuld" in out
    assert "Skuld nr" not in out


def test_medelstad_case_only_mal_nr():
    out = format_medelstad_results(_result([_medelstad_record(mal_typ="")]))
    assert "Case: 12" in out


def test_medelstad_none_valued_court_and_case_do_not_crash():
    rec = {
        "lopnr": 3,
        "norm_fornamn": "Anna",
        "ting_dag": None,
        "ting_typ": "Höstting",
        "mal_typ": None,
        "mal_nr": "9",
        "mal_referat": None,
    }
    out = format_medelstad_results(_result([rec]))
    assert "Court: Höstting" in out
    assert "Case: 9" in out
    assert "Summary:" not in out


def test_medelstad_long_summary_is_truncated_with_ellipsis():
    long_referat = "Y" * 300
    out = format_medelstad_results(_result([_medelstad_record(mal_referat=long_referat)]))
    assert "..." in out
    assert long_referat not in out
    # _truncate keeps max_len-3 chars + "..." for a 200 cap.
    assert "Y" * 197 + "..." in out


def test_medelstad_pagination_hint_when_more_pages():
    out = format_medelstad_results(_result([_medelstad_record()], total_hits=60, offset=25, limit=25))
    assert "More results available. Use offset=50 to see the next page." in out


def test_medelstad_no_pagination_hint_on_last_page():
    out = format_medelstad_results(_result([_medelstad_record()], total_hits=1, offset=0, limit=25))
    assert "More results available" not in out

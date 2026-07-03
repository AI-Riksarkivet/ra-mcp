"""Tests for the suffrage-mcp plain-text formatters.

The formatters are pure, synchronous functions that turn a ``SearchResult``
(carrying a list of plain ``dict`` records) into markdown-ish plain text for
MCP/LLM consumption. No network, no LanceDB, no mocks required.
"""

from ra_mcp_suffrage_lib.search_operations import SearchResult
from ra_mcp_suffrage_mcp.formatter import (
    _format_contribution,
    format_fkpr_results,
    format_rostratt_results,
)


def make_result(records, *, total_hits=None, keyword="test", offset=0, limit=25):
    """Build a SearchResult from a list of record dicts."""
    return SearchResult(
        records=records,
        total_hits=len(records) if total_hits is None else total_hits,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


ROSTRATT_FULL = {
    "fornamn": "Anna",
    "efternamn": "Svensson",
    "titel": "Fru",
    "yrke": "Lärarinna",
    "adress": "Storgatan 1",
    "ortens_namn": "Karlskrona",
    "lan": "Blekinge",
    "bidrag_kr": "5",
    "bidrag_ore": "50",
    "fodelseuppgift": "1880-03-14",
    "ovriga_anteckningar": "Aktiv i föreningen",
    "bild_id": "A0012345_00001",
}

FKPR_FULL = {
    "foernamn": "Maria",
    "efternamn": "Lindberg",
    "titel_yrke": "Sömmerska",
    "adress": "Kungsgatan 3",
    "anteckningar": "Kassör",
    "membership_years": [1911, 1913, 1914],
    "bild_id": "B0009876_00002",
}


# ---------------------------------------------------------------------------
# format_rostratt_results — empty result set
# ---------------------------------------------------------------------------


def test_format_rostratt_results_empty_no_offset():
    out = format_rostratt_results(make_result([], keyword="trolldom", offset=0))
    assert out == "No Rösträtt results found for 'trolldom'."


def test_format_rostratt_results_empty_with_offset():
    out = format_rostratt_results(make_result([], total_hits=3, keyword="Anna", offset=25))
    assert out == ("No more Rösträtt results for 'Anna' at offset 25. Total found: 3")


# ---------------------------------------------------------------------------
# format_rostratt_results — single record
# ---------------------------------------------------------------------------


def test_format_rostratt_results_single_record_full_fields():
    out = format_rostratt_results(make_result([ROSTRATT_FULL], keyword="kvinnor"))

    assert "Rösträtt search results for 'kvinnor'" in out
    assert "showing 1 of 1 records (offset 0)" in out
    assert "--- Anna Svensson ---" in out
    assert "Title: Fru" in out
    assert "Occupation: Lärarinna" in out
    assert "Address: Storgatan 1" in out
    assert "Town: Karlskrona, Blekinge" in out
    assert "Contribution: 5 kr 50 öre" in out
    assert "Birth info: 1880-03-14" in out
    assert "Notes: Aktiv i föreningen" in out
    assert "Source: https://sok.riksarkivet.se/bildvisning/A0012345_00001" in out
    assert "Tip: Use view_bild" in out


def test_format_rostratt_results_town_only_lan():
    rec = {"fornamn": "Bo", "efternamn": "Ek", "lan": "Blekinge"}
    out = format_rostratt_results(make_result([rec]))
    assert "Town: Blekinge" in out


def test_format_rostratt_results_town_only_ortens_namn():
    rec = {"fornamn": "Bo", "efternamn": "Ek", "ortens_namn": "Karlskrona"}
    out = format_rostratt_results(make_result([rec]))
    assert "Town: Karlskrona" in out


# ---------------------------------------------------------------------------
# format_rostratt_results — multiple records
# ---------------------------------------------------------------------------


def test_format_rostratt_results_multiple_records():
    second = {"fornamn": "Karin", "efternamn": "Berg"}
    out = format_rostratt_results(make_result([ROSTRATT_FULL, second], keyword="kvinnor"))
    assert "showing 2 of 2 records (offset 0)" in out
    assert "--- Anna Svensson ---" in out
    assert "--- Karin Berg ---" in out


# ---------------------------------------------------------------------------
# format_rostratt_results — missing / None optional fields
# ---------------------------------------------------------------------------


def test_format_rostratt_results_missing_optional_fields():
    rec = {"fornamn": "Bo", "efternamn": "Nilsson"}
    out = format_rostratt_results(make_result([rec]))

    assert "--- Bo Nilsson ---" in out
    # None of the optional labelled lines should be emitted.
    assert "Title:" not in out
    assert "Occupation:" not in out
    assert "Address:" not in out
    assert "Town:" not in out
    assert "Contribution:" not in out
    assert "Birth info:" not in out
    assert "Notes:" not in out
    # No bild_id -> no Source URL.
    assert "bildvisning" not in out


# ---------------------------------------------------------------------------
# format_rostratt_results — pagination footer
# ---------------------------------------------------------------------------


def test_format_rostratt_results_pagination_shown():
    out = format_rostratt_results(make_result([ROSTRATT_FULL], total_hits=30, keyword="kvinnor"))
    assert "showing 1 of 30 records" in out
    assert "More results available. Use offset=25 to see the next page." in out


def test_format_rostratt_results_pagination_absent_on_last_page():
    out = format_rostratt_results(make_result([ROSTRATT_FULL], total_hits=1, keyword="kvinnor"))
    assert "More results available" not in out


# ---------------------------------------------------------------------------
# format_fkpr_results — empty result set
# ---------------------------------------------------------------------------


def test_format_fkpr_results_empty_no_offset():
    out = format_fkpr_results(make_result([], keyword="Lindberg", offset=0))
    assert out == "No FKPR results found for 'Lindberg'."


def test_format_fkpr_results_empty_with_offset():
    out = format_fkpr_results(make_result([], total_hits=7, keyword="Lindberg", offset=25))
    assert out == ("No more FKPR results for 'Lindberg' at offset 25. Total found: 7")


# ---------------------------------------------------------------------------
# format_fkpr_results — single record
# ---------------------------------------------------------------------------


def test_format_fkpr_results_single_record_full_fields():
    out = format_fkpr_results(make_result([FKPR_FULL], keyword="göteborg"))

    assert "FKPR search results for 'göteborg'" in out
    assert "showing 1 of 1 records (offset 0)" in out
    assert "--- Maria Lindberg ---" in out
    assert "Title: Sömmerska" in out
    assert "Address: Kungsgatan 3" in out
    assert "Member: 1911, 1913, 1914" in out
    assert "Notes: Kassör" in out
    assert "Source: https://sok.riksarkivet.se/bildvisning/B0009876_00002" in out
    assert "Tip: Open the Source link" in out


# ---------------------------------------------------------------------------
# format_fkpr_results — multiple records
# ---------------------------------------------------------------------------


def test_format_fkpr_results_multiple_records():
    second = {"foernamn": "Elsa", "efternamn": "Holm", "membership_years": [1920]}
    out = format_fkpr_results(make_result([FKPR_FULL, second], keyword="göteborg"))
    assert "showing 2 of 2 records (offset 0)" in out
    assert "--- Maria Lindberg ---" in out
    assert "--- Elsa Holm ---" in out
    assert "Member: 1920" in out


# ---------------------------------------------------------------------------
# format_fkpr_results — missing / None optional fields
# ---------------------------------------------------------------------------


def test_format_fkpr_results_missing_optional_fields():
    rec = {"foernamn": "Karl", "efternamn": "Berg", "membership_years": []}
    out = format_fkpr_results(make_result([rec]))

    assert "--- Karl Berg ---" in out
    assert "Title:" not in out
    assert "Address:" not in out
    # Empty membership_years -> no Member line.
    assert "Member:" not in out
    assert "Notes:" not in out
    # No bild_id -> no Source URL.
    assert "bildvisning" not in out


def test_format_fkpr_results_missing_membership_years_key():
    # membership_years key entirely absent (defaults to []) -> no Member line.
    rec = {"foernamn": "Karl", "efternamn": "Berg"}
    out = format_fkpr_results(make_result([rec]))
    assert "--- Karl Berg ---" in out
    assert "Member:" not in out


# ---------------------------------------------------------------------------
# format_fkpr_results — pagination footer
# ---------------------------------------------------------------------------


def test_format_fkpr_results_pagination_shown():
    out = format_fkpr_results(make_result([FKPR_FULL], total_hits=40, keyword="göteborg"))
    assert "showing 1 of 40 records" in out
    assert "More results available. Use offset=25 to see the next page." in out


def test_format_fkpr_results_pagination_absent_on_last_page():
    out = format_fkpr_results(make_result([FKPR_FULL], total_hits=1, keyword="göteborg"))
    assert "More results available" not in out


# ---------------------------------------------------------------------------
# _format_contribution — all four kr/öre branches
# ---------------------------------------------------------------------------


def test_format_contribution_kr_and_ore():
    assert _format_contribution({"bidrag_kr": "5", "bidrag_ore": "50"}) == "5 kr 50 öre"


def test_format_contribution_kr_only():
    assert _format_contribution({"bidrag_kr": "5"}) == "5 kr"


def test_format_contribution_ore_only():
    assert _format_contribution({"bidrag_ore": "50"}) == "50 öre"


def test_format_contribution_none():
    assert _format_contribution({}) == ""

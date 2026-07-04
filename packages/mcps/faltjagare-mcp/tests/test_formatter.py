"""Tests for the Fältjägare plain-text result formatter.

``format_faltjagare_results`` is the only public function; it is a pure,
synchronous ``SearchResult -> str`` transform, so these are plain sync tests
with no network, LanceDB, or mocks. The private record helpers
(``_format_faltjagare_record`` / ``_append_if``) are exercised through the
public entry point.

Records passed to the formatter are raw LanceDB rows (plain ``dict``), read via
``dict.get`` — the field names match ``FaltjagareRecord`` in faltjagare-lib.
"""

from ra_mcp_faltjagare_lib.search_operations import SearchResult
from ra_mcp_faltjagare_mcp.formatter import format_faltjagare_results


# ---------------------------------------------------------------------------
# Helpers / sample data
# ---------------------------------------------------------------------------

FULL_RECORD: dict = {
    "soldatnamn": "Modig",
    "foernamn": "Anders",
    "familjenamn": "Andersson",
    "kompani": "Brunflo kompani",
    "befattning": "Soldat",
    "rotens_socken": "Brunflo",
    "region": "Jämtland",
    "from_tjaenst": "1710",
    "till_tjaenst": "1718",
    "foedelsedatum": "1685",
    "foedelsesocken": "Brunflo",
    "platsen_stupade": "Fredrikshald",
    "doedsort": "Fredrikshald",
    "doedsdatum": "1718",
    "oevrig_information": "Stupade vid belägringen av Fredrikshald",
}


def make_result(
    records: list[dict],
    *,
    keyword: str = "trolldom",
    total_hits: int | None = None,
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


# ---------------------------------------------------------------------------
# Empty / no-results branches
# ---------------------------------------------------------------------------


def test_format_no_results_offset_zero() -> None:
    out = format_faltjagare_results(make_result([], keyword="Stockholm", offset=0))
    assert out == "No Fältjägare results found for 'Stockholm'."


def test_format_no_more_results_with_offset() -> None:
    out = format_faltjagare_results(make_result([], keyword="Modig", total_hits=42, offset=25))
    assert "No more Fältjägare results for 'Modig' at offset 25" in out
    assert "Total found: 42" in out


def test_format_no_results_keyword_is_quoted_exactly() -> None:
    out = format_faltjagare_results(make_result([], keyword="Brunflo kompani"))
    assert "'Brunflo kompani'" in out


# ---------------------------------------------------------------------------
# Header / counts
# ---------------------------------------------------------------------------


def test_format_single_record_header_counts() -> None:
    out = format_faltjagare_results(make_result([FULL_RECORD], keyword="Modig", total_hits=1, offset=0))
    header = out.splitlines()[0]
    assert "Fältjägare search results for 'Modig'" in header
    assert "showing 1 of 1 records" in header
    assert "offset 0" in header


def test_format_multiple_records_header_counts() -> None:
    records = [FULL_RECORD, FULL_RECORD, FULL_RECORD]
    out = format_faltjagare_results(make_result(records, keyword="soldat", total_hits=100, offset=25, limit=25))
    header = out.splitlines()[0]
    assert "showing 3 of 100 records" in header
    assert "offset 25" in header


def test_format_multiple_records_all_rendered() -> None:
    records = [
        {"soldatnamn": "Modig"},
        {"soldatnamn": "Hurtig"},
        {"soldatnamn": "Rask"},
    ]
    out = format_faltjagare_results(make_result(records))
    assert "--- Modig ---" in out
    assert "--- Hurtig ---" in out
    assert "--- Rask ---" in out


# ---------------------------------------------------------------------------
# Pagination hint
# ---------------------------------------------------------------------------


def test_format_more_results_hint_when_more_pages() -> None:
    # offset 0 + limit 25 = next_offset 25 < total_hits 100 -> hint present
    out = format_faltjagare_results(make_result([FULL_RECORD], total_hits=100, offset=0, limit=25))
    assert "More results available. Use offset=25 to see the next page." in out


def test_format_no_hint_on_last_page() -> None:
    # next_offset 50 >= total_hits 30 -> no hint
    out = format_faltjagare_results(make_result([FULL_RECORD], total_hits=30, offset=25, limit=25))
    assert "More results available" not in out


def test_format_no_hint_when_exactly_exhausted() -> None:
    # next_offset 25 == total_hits 25 -> not strictly less, no hint
    out = format_faltjagare_results(make_result([FULL_RECORD], total_hits=25, offset=0, limit=25))
    assert "More results available" not in out


# ---------------------------------------------------------------------------
# Full record — every labelled field rendered
# ---------------------------------------------------------------------------


def test_format_full_record_renders_all_labels() -> None:
    out = format_faltjagare_results(make_result([FULL_RECORD]))
    assert "--- Modig (Anders Andersson) ---" in out
    assert "Rank: Soldat" in out
    assert "Company: Brunflo kompani" in out
    assert "Parish: Brunflo, Jämtland" in out
    assert "Service: 1710 - 1718" in out
    assert "Born: 1685, Brunflo" in out
    assert "Died: 1718, Fredrikshald" in out
    assert "Killed: Fredrikshald" in out
    assert "Info: Stupade vid belägringen av Fredrikshald" in out


# ---------------------------------------------------------------------------
# Name header variants
# ---------------------------------------------------------------------------


def test_format_name_both_first_and_family() -> None:
    rec = {"soldatnamn": "Modig", "foernamn": "Anders", "familjenamn": "Andersson"}
    out = format_faltjagare_results(make_result([rec]))
    assert "--- Modig (Anders Andersson) ---" in out


def test_format_name_only_first_name() -> None:
    rec = {"soldatnamn": "Modig", "foernamn": "Anders"}
    out = format_faltjagare_results(make_result([rec]))
    assert "--- Modig (Anders) ---" in out


def test_format_name_only_family_name() -> None:
    rec = {"soldatnamn": "Modig", "familjenamn": "Andersson"}
    out = format_faltjagare_results(make_result([rec]))
    assert "--- Modig (Andersson) ---" in out


def test_format_name_no_extra_when_only_soldatnamn() -> None:
    rec = {"soldatnamn": "Modig"}
    out = format_faltjagare_results(make_result([rec]))
    assert "--- Modig ---" in out
    assert "(" not in out.split("--- Modig")[1].splitlines()[0]


def test_format_name_empty_soldatnamn_still_renders_marker() -> None:
    # Missing soldatnamn -> empty; only foernamn present.
    rec = {"foernamn": "Anders"}
    out = format_faltjagare_results(make_result([rec]))
    assert "---  (Anders) ---" in out


# ---------------------------------------------------------------------------
# Parish / Region branch
# ---------------------------------------------------------------------------


def test_format_parish_with_region() -> None:
    rec = {"soldatnamn": "X", "rotens_socken": "Brunflo", "region": "Jämtland"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Parish: Brunflo, Jämtland" in out


def test_format_parish_only() -> None:
    rec = {"soldatnamn": "X", "rotens_socken": "Brunflo"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Parish: Brunflo" in out
    assert "Parish: Brunflo," not in out


def test_format_region_only_uses_region_label() -> None:
    rec = {"soldatnamn": "X", "region": "Jämtland"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Region: Jämtland" in out
    assert "Parish:" not in out


def test_format_no_parish_or_region_line_when_both_missing() -> None:
    rec = {"soldatnamn": "X"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Parish:" not in out
    assert "Region:" not in out


# ---------------------------------------------------------------------------
# Service range
# ---------------------------------------------------------------------------


def test_format_service_full_range() -> None:
    rec = {"soldatnamn": "X", "from_tjaenst": "1710", "till_tjaenst": "1718"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Service: 1710 - 1718" in out


def test_format_service_open_ended_from_only() -> None:
    rec = {"soldatnamn": "X", "from_tjaenst": "1710"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Service: 1710 - " in out


def test_format_service_open_ended_till_only() -> None:
    rec = {"soldatnamn": "X", "till_tjaenst": "1718"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Service:  - 1718" in out


def test_format_no_service_line_when_both_missing() -> None:
    rec = {"soldatnamn": "X"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Service:" not in out


# ---------------------------------------------------------------------------
# Born branch
# ---------------------------------------------------------------------------


def test_format_born_date_and_place() -> None:
    rec = {"soldatnamn": "X", "foedelsedatum": "1685", "foedelsesocken": "Brunflo"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Born: 1685, Brunflo" in out


def test_format_born_date_only() -> None:
    rec = {"soldatnamn": "X", "foedelsedatum": "1685"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Born: 1685" in out
    assert "Born: 1685," not in out


def test_format_born_place_only() -> None:
    rec = {"soldatnamn": "X", "foedelsesocken": "Brunflo"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Born: Brunflo" in out


def test_format_no_born_line_when_both_missing() -> None:
    rec = {"soldatnamn": "X"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Born:" not in out


# ---------------------------------------------------------------------------
# Died branch
# ---------------------------------------------------------------------------


def test_format_died_date_and_place() -> None:
    rec = {"soldatnamn": "X", "doedsdatum": "1718", "doedsort": "Fredrikshald"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Died: 1718, Fredrikshald" in out


def test_format_died_date_only() -> None:
    rec = {"soldatnamn": "X", "doedsdatum": "1718"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Died: 1718" in out
    assert "Died: 1718," not in out


def test_format_died_place_only() -> None:
    rec = {"soldatnamn": "X", "doedsort": "Fredrikshald"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Died: Fredrikshald" in out


def test_format_no_died_line_when_both_missing() -> None:
    rec = {"soldatnamn": "X"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Died:" not in out


# ---------------------------------------------------------------------------
# Optional single-value fields: Rank / Company / Killed / Info
# ---------------------------------------------------------------------------


def test_format_omits_optional_labels_when_missing() -> None:
    rec = {"soldatnamn": "Modig"}
    out = format_faltjagare_results(make_result([rec]))
    assert "Rank:" not in out
    assert "Company:" not in out
    assert "Killed:" not in out
    assert "Info:" not in out


def test_format_killed_and_info_rendered() -> None:
    rec = {
        "soldatnamn": "Modig",
        "platsen_stupade": "Poltava",
        "oevrig_information": "Tillfångatagen",
    }
    out = format_faltjagare_results(make_result([rec]))
    assert "Killed: Poltava" in out
    assert "Info: Tillfångatagen" in out


# ---------------------------------------------------------------------------
# Minimal record with entirely missing keys (dict.get must not KeyError)
# ---------------------------------------------------------------------------


def test_format_empty_dict_record_does_not_crash() -> None:
    out = format_faltjagare_results(make_result([{}]))
    # Empty soldatnamn and no name parts -> bare marker.
    assert "---  ---" in out
    # None of the optional labels should appear.
    for label in ("Rank:", "Company:", "Parish:", "Region:", "Service:", "Born:", "Died:", "Killed:", "Info:"):
        assert label not in out


def test_format_minimal_record_only_name_line_and_blank() -> None:
    out = format_faltjagare_results(make_result([{"soldatnamn": "Modig"}], keyword="Modig", total_hits=1))
    lines = out.splitlines()
    assert lines[0].startswith("Fältjägare search results for 'Modig'")
    assert lines[1] == ""  # blank line after header
    assert "--- Modig ---" in lines
    # A trailing blank line is appended after each record -> output ends with newline.
    assert out.endswith("\n")

"""Tests for the Filmcensur plain-text formatter.

The formatter is a pure sync function that turns a ``SearchResult`` (whose
``records`` are plain dicts, as returned by LanceDB ``.to_list()``) into a
plain-text/markdown string for MCP/LLM consumption. No network, no LanceDB.
"""

from ra_mcp_filmcensur_lib.search_operations import SearchResult
from ra_mcp_filmcensur_mcp.formatter import format_filmreg_results


def _record(**overrides) -> dict:
    """Build a realistic Filmreg record dict (values mirror the lib fixtures)."""
    base = {
        "granskningsnummer": 1001,
        "titel_org": "The Great Train Robbery",
        "titel_svensk": "Det stora tågrånet",
        "produktionsaar": "1903",
        "filmkategori": "Spelfilm",
        "filmtyp": "Stumfilm",
        "produktionsland": "USA",
        "fri_text": "En brottslingsliga rånar ett tåg i västra USA",
        "beslutsdatum": "1911-03-15",
        "aaldersgraens": "Barntillåten",
        "klipp_antal": "0",
        "producent": "Edison Manufacturing",
        "beslut_laengd": "12 min",
    }
    base.update(overrides)
    return base


def _result(
    records: list[dict],
    *,
    keyword: str = "trolldom",
    total_hits: int | None = None,
    offset: int = 0,
    limit: int = 25,
) -> SearchResult:
    """Build a SearchResult around the given records."""
    if total_hits is None:
        total_hits = len(records)
    return SearchResult(
        records=records,
        total_hits=total_hits,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


# --- empty / no-results boundaries -----------------------------------------


def test_format_filmreg_results_no_results_offset_zero():
    out = format_filmreg_results(_result([], keyword="drakar", total_hits=0, offset=0))
    assert out == "No Filmreg results found for 'drakar'."


def test_format_filmreg_results_no_more_results_with_offset():
    out = format_filmreg_results(
        _result([], keyword="drakar", total_hits=42, offset=25),
    )
    assert "No more Filmreg results for 'drakar' at offset 25" in out
    assert "Total found: 42" in out


def test_format_filmreg_results_empty_offset_zero_ignores_total():
    # At offset 0 with no records we always report the plain "not found" message.
    out = format_filmreg_results(_result([], keyword="x", total_hits=7, offset=0))
    assert out == "No Filmreg results found for 'x'."
    assert "offset" not in out


# --- single record: header + every label -----------------------------------


def test_format_filmreg_results_single_record_header():
    out = format_filmreg_results(_result([_record()], keyword="tåg"))
    assert "Filmreg search results for 'tåg': showing 1 of 1 records (offset 0)" in out


def test_format_filmreg_results_single_record_film_header_uses_granskningsnummer():
    out = format_filmreg_results(_result([_record(granskningsnummer=1004)]))
    assert "--- Film 1004 ---" in out


def test_format_filmreg_results_single_record_all_labels_present():
    out = format_filmreg_results(_result([_record()]))
    assert "Title: The Great Train Robbery" in out
    assert "Swedish title: Det stora tågrånet" in out
    assert "Year: 1903" in out
    assert "Category: Spelfilm / Stumfilm" in out
    assert "Country: USA" in out
    assert "Producer: Edison Manufacturing" in out
    assert "Age rating: Barntillåten" in out
    assert "Duration: 12 min" in out
    assert "Decision: 1911-03-15" in out
    assert "Description: En brottslingsliga rånar ett tåg i västra USA" in out


def test_format_filmreg_results_cuts_zero_string_is_shown():
    # "0" is a truthy string, so the Cuts line must still render.
    out = format_filmreg_results(_result([_record(klipp_antal="0")]))
    assert "Cuts: 0" in out


# --- multiple records ------------------------------------------------------


def test_format_filmreg_results_multiple_records_all_rendered():
    records = [
        _record(granskningsnummer=1001, titel_org="The Great Train Robbery"),
        _record(granskningsnummer=1004, titel_org="Metropolis"),
    ]
    out = format_filmreg_results(_result(records))
    assert "showing 2 of 2 records" in out
    assert "--- Film 1001 ---" in out
    assert "--- Film 1004 ---" in out
    assert "Title: The Great Train Robbery" in out
    assert "Title: Metropolis" in out


# --- missing / None optional fields ----------------------------------------


def test_format_filmreg_results_missing_optional_fields_omitted():
    # Only granskningsnummer present; every optional field defaults to "".
    out = format_filmreg_results(_result([{"granskningsnummer": 2000}]))
    assert "--- Film 2000 ---" in out
    for label in (
        "Title:",
        "Swedish title:",
        "Year:",
        "Category:",
        "Country:",
        "Producer:",
        "Age rating:",
        "Cuts:",
        "Duration:",
        "Decision:",
        "Description:",
    ):
        assert label not in out


def test_format_filmreg_results_missing_granskningsnummer_uses_placeholder():
    out = format_filmreg_results(_result([{"titel_org": "Untitled"}]))
    assert "--- Film ? ---" in out
    assert "Title: Untitled" in out


def test_format_filmreg_results_empty_string_fields_omitted():
    rec = _record(titel_svensk="", produktionsland="", producent="")
    out = format_filmreg_results(_result([rec]))
    assert "Swedish title:" not in out
    assert "Country:" not in out
    assert "Producer:" not in out
    # Present fields still render.
    assert "Title: The Great Train Robbery" in out


# --- category composition (kategori / filmtyp) -----------------------------


def test_format_filmreg_results_category_both_parts_joined():
    out = format_filmreg_results(
        _result([_record(filmkategori="Spelfilm", filmtyp="Stumfilm")]),
    )
    assert "Category: Spelfilm / Stumfilm" in out


def test_format_filmreg_results_category_kategori_only():
    out = format_filmreg_results(
        _result([_record(filmkategori="Dokumentär", filmtyp="")]),
    )
    assert "Category: Dokumentär" in out
    assert " / " not in out


def test_format_filmreg_results_category_filmtyp_only():
    out = format_filmreg_results(
        _result([_record(filmkategori="", filmtyp="Ljudfilm")]),
    )
    assert "Category: Ljudfilm" in out


def test_format_filmreg_results_category_omitted_when_both_empty():
    out = format_filmreg_results(
        _result([_record(filmkategori="", filmtyp="")]),
    )
    assert "Category:" not in out


# --- description truncation (_truncate at 200 chars) -----------------------


def test_format_filmreg_results_description_truncated_when_long():
    long_text = "A" * 250
    out = format_filmreg_results(_result([_record(fri_text=long_text)]))
    # _truncate keeps first 197 chars then appends "..." for a 200-char body.
    assert "Description: " + ("A" * 197) + "..." in out
    # The full 250-char run must not survive.
    assert "A" * 201 not in out


def test_format_filmreg_results_description_not_truncated_when_short():
    short_text = "A short synopsis."
    out = format_filmreg_results(_result([_record(fri_text=short_text)]))
    assert f"Description: {short_text}" in out
    assert "..." not in out


# --- pagination footer -----------------------------------------------------


def test_format_filmreg_results_more_available_footer():
    out = format_filmreg_results(
        _result([_record()], total_hits=100, offset=0, limit=25),
    )
    assert "More results available. Use offset=25 to see the next page." in out


def test_format_filmreg_results_more_available_respects_offset():
    out = format_filmreg_results(
        _result([_record()], total_hits=100, offset=25, limit=25),
    )
    assert "Use offset=50 to see the next page." in out


def test_format_filmreg_results_no_footer_on_last_page():
    out = format_filmreg_results(
        _result([_record()], total_hits=1, offset=0, limit=25),
    )
    assert "More results available" not in out


def test_format_filmreg_results_header_reports_showing_total_and_offset():
    records = [_record(granskningsnummer=n) for n in (10, 11, 12)]
    out = format_filmreg_results(
        _result(records, keyword="film", total_hits=57, offset=25, limit=25),
    )
    assert "Filmreg search results for 'film': showing 3 of 57 records (offset 25)" in out

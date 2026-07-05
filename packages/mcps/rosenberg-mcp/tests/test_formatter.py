"""Tests for the Rosenberg plain-text formatter.

``format_rosenberg_results`` is a pure, synchronous function that turns a
``SearchResult`` (records are plain LanceDB dicts) into a plain-text/markdown
string for MCP/LLM consumption. These tests exercise it across boundaries:
empty result sets (with and without an offset), a single fully-populated
record, multiple records, records missing optional fields, the ``harad`` /
``tingslag`` "Hundred" join, description truncation, industry flag collection,
and pagination hints.
"""

from ra_mcp_rosenberg_lib.search_operations import SearchResult
from ra_mcp_rosenberg_mcp.formatter import format_rosenberg_results


# ---------------------------------------------------------------------------
# Helpers / mock data (self-contained)
# ---------------------------------------------------------------------------

# ASCII field names for the boolean industry flags, matching RosenbergRecord.
_INDUSTRY_FIELDS: list[str] = [
    "kalkbranning",
    "tandstikor",
    "fyr",
    "farjstalle",
    "fisk",
    "branneri",
    "stambana",
    "jernverk",
    "tegelbruk",
    "mjolsfabrik",
    "gjuteri",
    "gastgifveri",
    "sateri",
    "jernvag",
    "grufva",
    "sag",
    "qvarn",
]


def _make_record(**overrides: object) -> dict:
    """Build a realistic Rosenberg record dict (all industry flags off)."""
    rec: dict = {
        "post_id": 1,
        "url": "http://example.com/1",
        "plats": "",
        "forsamling": "",
        "harad": "",
        "tingslag": "",
        "lan": "",
        "beskrivning": "",
    }
    for field in _INDUSTRY_FIELDS:
        rec[field] = ""
    rec.update(overrides)
    return rec


def _make_result(records: list[dict], **overrides: object) -> SearchResult:
    """Build a SearchResult around the given records with sensible defaults."""
    params: dict = {
        "records": records,
        "total_hits": len(records),
        "keyword": "stockholm",
        "offset": 0,
        "limit": 25,
    }
    params.update(overrides)
    return SearchResult(**params)  # type: ignore[arg-type]


STOCKHOLM = _make_record(
    post_id=1,
    plats="Stockholm",
    forsamling="Klara",
    harad="Stockholms stad",
    tingslag="",
    lan="Stockholms län",
    beskrivning="Rikets hufvudstad vid Mälarens utlopp i Salt-sjön",
    gastgifveri="1",
    sag="1",
)


# ---------------------------------------------------------------------------
# Empty result set
# ---------------------------------------------------------------------------


def test_no_results_at_first_page():
    result = _make_result([], total_hits=0, keyword="trolldom", offset=0)
    out = format_rosenberg_results(result)
    assert out == "No Rosenberg results found for 'trolldom'."


def test_no_results_past_offset_reports_total():
    result = _make_result([], total_hits=42, keyword="trolldom", offset=50)
    out = format_rosenberg_results(result)
    assert "No more Rosenberg results for 'trolldom' at offset 50" in out
    assert "Total found: 42" in out


# ---------------------------------------------------------------------------
# Header line
# ---------------------------------------------------------------------------


def test_header_reports_counts_and_offset():
    result = _make_result([STOCKHOLM], total_hits=7, offset=0)
    out = format_rosenberg_results(result)
    assert "Rosenberg search results for 'stockholm': showing 1 of 7 records (offset 0)" in out


# ---------------------------------------------------------------------------
# Single fully-populated record
# ---------------------------------------------------------------------------


def test_single_record_renders_all_fields():
    result = _make_result([STOCKHOLM], total_hits=1)
    out = format_rosenberg_results(result)
    assert "--- Rosenberg 1 ---" in out
    assert "Place: Stockholm" in out
    assert "Parish: Klara" in out
    assert "County: Stockholms län" in out
    assert "Description: Rikets hufvudstad vid Mälarens utlopp i Salt-sjön" in out


def test_single_record_hundred_only_harad():
    result = _make_result([STOCKHOLM])
    out = format_rosenberg_results(result)
    # tingslag is empty, so only harad appears (no trailing separator).
    assert "Hundred: Stockholms stad" in out
    assert "Hundred: Stockholms stad /" not in out


def test_single_record_industries_line():
    result = _make_result([STOCKHOLM])
    out = format_rosenberg_results(result)
    # INDUSTRY_DISPLAY ordering places Gästgifveri before Såg.
    assert "Industries: Gästgifveri, Såg" in out


# ---------------------------------------------------------------------------
# Hundred join (harad / tingslag)
# ---------------------------------------------------------------------------


def test_hundred_joins_harad_and_tingslag():
    rec = _make_record(harad="Vemmenhögs härad", tingslag="Vemmenhögs tingslag")
    out = format_rosenberg_results(_make_result([rec]))
    assert "Hundred: Vemmenhögs härad / Vemmenhögs tingslag" in out


def test_hundred_only_tingslag_present():
    rec = _make_record(harad="", tingslag="Solberga tingslag")
    out = format_rosenberg_results(_make_result([rec]))
    assert "Hundred: Solberga tingslag" in out


def test_no_hundred_line_when_both_empty():
    rec = _make_record(harad="", tingslag="")
    out = format_rosenberg_results(_make_result([rec]))
    assert "Hundred:" not in out


# ---------------------------------------------------------------------------
# Missing / None optional fields
# ---------------------------------------------------------------------------


def test_minimal_record_only_emits_header():
    rec = _make_record(post_id=99)  # every other display field empty
    out = format_rosenberg_results(_make_result([rec]))
    assert "--- Rosenberg 99 ---" in out
    assert "Place:" not in out
    assert "Parish:" not in out
    assert "County:" not in out
    assert "Description:" not in out
    assert "Industries:" not in out
    assert "Hundred:" not in out


def test_record_missing_post_id_uses_placeholder():
    # A dict with no post_id key at all -> "?" fallback via rec.get(..., "?").
    rec = {"plats": "Okänd ort"}
    out = format_rosenberg_results(_make_result([rec]))
    assert "--- Rosenberg ? ---" in out
    assert "Place: Okänd ort" in out


def test_record_with_empty_strings_skips_optional_lines():
    rec = _make_record(post_id=5, plats="Bara plats", lan="")
    out = format_rosenberg_results(_make_result([rec]))
    assert "Place: Bara plats" in out
    assert "County:" not in out


# ---------------------------------------------------------------------------
# Description truncation
# ---------------------------------------------------------------------------


def test_long_description_is_truncated_to_300_with_ellipsis():
    long_text = "A" * 500
    rec = _make_record(beskrivning=long_text)
    out = format_rosenberg_results(_make_result([rec]))
    # Extract the Description line and check length semantics.
    desc_line = next(line for line in out.splitlines() if line.startswith("Description: "))
    payload = desc_line[len("Description: ") :]
    assert payload.endswith("...")
    assert len(payload) == 300
    assert payload == "A" * 297 + "..."


def test_short_description_is_not_truncated():
    rec = _make_record(beskrivning="Kort beskrivning")
    out = format_rosenberg_results(_make_result([rec]))
    assert "Description: Kort beskrivning" in out
    assert "..." not in out


# ---------------------------------------------------------------------------
# Multiple records
# ---------------------------------------------------------------------------


def test_multiple_records_all_rendered():
    rec_a = _make_record(post_id=1, plats="Alfa")
    rec_b = _make_record(post_id=2, plats="Beta")
    rec_c = _make_record(post_id=3, plats="Gamma")
    out = format_rosenberg_results(_make_result([rec_a, rec_b, rec_c], total_hits=3))
    assert "--- Rosenberg 1 ---" in out
    assert "--- Rosenberg 2 ---" in out
    assert "--- Rosenberg 3 ---" in out
    assert "Place: Alfa" in out
    assert "Place: Beta" in out
    assert "Place: Gamma" in out
    assert "showing 3 of 3 records" in out


# ---------------------------------------------------------------------------
# Pagination hint
# ---------------------------------------------------------------------------


def test_more_results_hint_when_next_page_available():
    result = _make_result([STOCKHOLM], total_hits=50, offset=0, limit=25)
    out = format_rosenberg_results(result)
    assert "More results available. Use offset=25 to see the next page." in out


def test_no_more_results_hint_on_last_page():
    result = _make_result([STOCKHOLM], total_hits=1, offset=0, limit=25)
    out = format_rosenberg_results(result)
    assert "More results available" not in out


def test_pagination_hint_uses_offset_plus_limit():
    result = _make_result([STOCKHOLM], total_hits=100, offset=25, limit=25)
    out = format_rosenberg_results(result)
    assert "Use offset=50 to see the next page." in out

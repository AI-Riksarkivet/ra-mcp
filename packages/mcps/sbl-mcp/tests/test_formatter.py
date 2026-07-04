"""Tests for the SBL result formatter (pure sync functions, no network/LanceDB)."""

from __future__ import annotations

import pytest

from ra_mcp_sbl_lib.search_operations import SearchResult
from ra_mcp_sbl_mcp.formatter import _format_date, format_sbl_results


def _record(**overrides: object) -> dict:
    """Build a realistic SBL record dict, overriding chosen fields.

    Field names match the SBLRecord model (records are serialized to dicts and
    read via ``.get()`` by the formatter).
    """
    base: dict = {
        "given_name": "Carl",
        "surname": "Linnaeus",
        "gender": "m",
        "article_type": "Main article",
        "occupation": "botanist",
        "birth_year_prefix": "",
        "birth_year": 1707,
        "birth_month": 5,
        "birth_day": 23,
        "birth_place": "Rashult",
        "death_year_prefix": "",
        "death_year": 1778,
        "death_month": 1,
        "death_day": 10,
        "death_place": "Uppsala",
        "cv": "Swedish botanist and zoologist.",
        "sbl_uri": "https://sok.riksarkivet.se/sbl/Presentation.aspx?id=9421",
    }
    base.update(overrides)
    return base


def _result(records: list[dict], *, keyword: str = "Linnaeus", total_hits: int | None = None, offset: int = 0, limit: int = 25) -> SearchResult:
    return SearchResult(
        records=records,
        total_hits=len(records) if total_hits is None else total_hits,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


# --------------------------------------------------------------------------
# _format_date
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "year,month,day,prefix,expected",
    [
        pytest.param(None, None, None, "", "", id="no-year"),
        pytest.param(1819, None, None, "", "1819", id="year-only"),
        pytest.param(1819, 5, None, "", "1819-05", id="year-month"),
        pytest.param(1819, 5, 17, "", "1819-05-17", id="full-date"),
        pytest.param(1750, None, None, "~", "~1750", id="prefix"),
        pytest.param(1707, 5, 23, "", "1707-05-23", id="zero-padded-month-day"),
        pytest.param(1819, None, 17, "", "1819", id="day-without-month-ignored"),
    ],
)
def test_format_date_variants(year, month, day, prefix, expected):
    assert _format_date(year, month, day, prefix=prefix) == expected


# --------------------------------------------------------------------------
# format_sbl_results: empty / no-results boundaries
# --------------------------------------------------------------------------


def test_format_sbl_results_no_results_at_offset_zero():
    out = format_sbl_results(_result([], keyword="trolldom", total_hits=0, offset=0))
    assert out == "No SBL results found for 'trolldom'."


def test_format_sbl_results_no_more_results_at_nonzero_offset():
    out = format_sbl_results(_result([], keyword="trolldom", total_hits=42, offset=25))
    assert "No more SBL results for 'trolldom' at offset 25" in out
    assert "Total found: 42" in out


# --------------------------------------------------------------------------
# format_sbl_results: single record
# --------------------------------------------------------------------------


def test_format_sbl_results_single_record_full_fields():
    out = format_sbl_results(_result([_record()]))
    assert "SBL search results for 'Linnaeus': showing 1 of 1 records (offset 0)" in out
    assert "--- Carl Linnaeus ---" in out
    assert "Gender: Male" in out
    assert "Occupation: botanist" in out
    assert "Born: 1707-05-23, Rashult" in out
    assert "Died: 1778-01-10, Uppsala" in out
    assert "CV: Swedish botanist and zoologist." in out
    assert "SBL: https://sok.riksarkivet.se/sbl/Presentation.aspx?id=9421" in out


def test_format_sbl_results_female_gender_label():
    out = format_sbl_results(_result([_record(given_name="Selma", surname="Lagerlof", gender="f")]))
    assert "Gender: Female" in out


def test_format_sbl_results_dash_gender_omitted():
    out = format_sbl_results(_result([_record(gender="-")]))
    assert "Gender:" not in out


def test_format_sbl_results_unknown_gender_passthrough():
    out = format_sbl_results(_result([_record(gender="x")]))
    assert "Gender: x" in out


def test_format_sbl_results_family_article_type_shown():
    out = format_sbl_results(_result([_record(article_type="Family article")]))
    assert "Type: Family article" in out


def test_format_sbl_results_non_family_article_type_hidden():
    out = format_sbl_results(_result([_record(article_type="Main article")]))
    assert "Type:" not in out


def test_format_sbl_results_surname_only_name():
    out = format_sbl_results(_result([_record(given_name="", surname="Anonymous")]))
    assert "--- Anonymous ---" in out


def test_format_sbl_results_birth_year_prefix_rendered():
    out = format_sbl_results(_result([_record(birth_year_prefix="~", birth_year=1750, birth_month=None, birth_day=None, birth_place="")]))
    assert "Born: ~1750" in out


def test_format_sbl_results_birth_place_without_year():
    out = format_sbl_results(_result([_record(birth_year=None, birth_month=None, birth_day=None, birth_place="Stockholm")]))
    assert "Born: Stockholm" in out


# --------------------------------------------------------------------------
# format_sbl_results: CV truncation boundary
# --------------------------------------------------------------------------


def test_format_sbl_results_long_cv_truncated_at_200():
    long_cv = "A" * 250
    out = format_sbl_results(_result([_record(cv=long_cv)]))
    assert "CV: " + "A" * 200 + "..." in out
    assert "A" * 201 not in out


def test_format_sbl_results_short_cv_not_truncated():
    out = format_sbl_results(_result([_record(cv="Short bio")]))
    assert "CV: Short bio" in out
    assert "CV: Short bio..." not in out


# --------------------------------------------------------------------------
# format_sbl_results: missing / None optional fields
# --------------------------------------------------------------------------


def test_format_sbl_results_minimal_record_only_name():
    # Record dict with only a surname; every other field absent from the dict.
    out = format_sbl_results(_result([{"surname": "Nilsson"}]))
    assert "--- Nilsson ---" in out
    assert "Gender:" not in out
    assert "Occupation:" not in out
    assert "Born:" not in out
    assert "Died:" not in out
    assert "CV:" not in out
    assert "SBL:" not in out


def test_format_sbl_results_none_dates_omit_born_died():
    rec = _record(
        birth_year=None,
        birth_month=None,
        birth_day=None,
        birth_place="",
        death_year=None,
        death_month=None,
        death_day=None,
        death_place="",
    )
    out = format_sbl_results(_result([rec]))
    assert "Born:" not in out
    assert "Died:" not in out


def test_format_sbl_results_empty_optional_strings_omitted():
    rec = _record(occupation="", cv="", sbl_uri="")
    out = format_sbl_results(_result([rec]))
    assert "Occupation:" not in out
    assert "CV:" not in out
    assert "SBL:" not in out


# --------------------------------------------------------------------------
# format_sbl_results: multiple records + pagination
# --------------------------------------------------------------------------


def test_format_sbl_results_multiple_records_all_shown():
    records = [
        _record(given_name="Carl", surname="Linnaeus"),
        _record(given_name="Selma", surname="Lagerlof", gender="f"),
        _record(given_name="Alfred", surname="Nobel"),
    ]
    out = format_sbl_results(_result(records, keyword="swede", total_hits=3))
    assert "showing 3 of 3 records" in out
    assert "--- Carl Linnaeus ---" in out
    assert "--- Selma Lagerlof ---" in out
    assert "--- Alfred Nobel ---" in out


def test_format_sbl_results_pagination_hint_when_more_available():
    records = [_record()]
    out = format_sbl_results(_result(records, total_hits=100, offset=0, limit=25))
    assert "More results available. Use offset=25 to see the next page." in out


def test_format_sbl_results_no_pagination_hint_on_last_page():
    records = [_record()]
    out = format_sbl_results(_result(records, total_hits=10, offset=0, limit=25))
    assert "More results available" not in out

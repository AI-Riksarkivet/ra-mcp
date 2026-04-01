"""Tests for FaltjagareRecord Pydantic model."""

import pytest

from ra_mcp_faltjagare_lib.models import FaltjagareRecord, _clean


# ---------------------------------------------------------------------------
# Test data: soldier with all fields populated
# ---------------------------------------------------------------------------

FULL_ROW: dict[str, str] = {
    "Soldatnamn": "Modig",
    "Foernamn": "Anders",
    "Soldatens_familjenamn": "Andersson",
    "Kompani": "Brunflo kompani",
    "Befattning_regemente": "Soldat",
    "Rotens_socken": "Brunflo",
    "Region": "Jämtland",
    "From_tjaenst": "1710",
    "Slutdatum_tjaenstgoeringsperiod": "1718",
    "Soldatens_foedelsedatum": "1685",
    "Soldatens_foedelsesocken": "Brunflo",
    "Soldatens_foedelseregion": "Jämtland",
    "Platsen_stupade": "Fredrikshald",
    "Soldatens_doedsort": "NULL",
    "Soldatens_doedsdatum": "1718",
    "Oevrig_information": "Stupade vid belägringen av Fredrikshald",
    "Kommentar_startdatum ": "NULL",
}

# ---------------------------------------------------------------------------
# Test data: record with many NULL/<okänd> fields
# ---------------------------------------------------------------------------

MINIMAL_ROW: dict[str, str] = {
    "Soldatnamn": "Hurtig",
    "Foernamn": "Olof",
    "Soldatens_familjenamn": "NULL",
    "Kompani": "Revsunds kompani",
    "Befattning_regemente": "Soldat",
    "Rotens_socken": "Revsund",
    "Region": "Jämtland",
    "From_tjaenst": "1705",
    "Slutdatum_tjaenstgoeringsperiod": "1710",
    "Soldatens_foedelsedatum": "NULL",
    "Soldatens_foedelsesocken": "Revsund",
    "Soldatens_foedelseregion": "Jämtland",
    "Platsen_stupade": "NULL",
    "Soldatens_doedsort": "NULL",
    "Soldatens_doedsdatum": "NULL",
    "Oevrig_information": "<okänd>",
    "Kommentar_startdatum ": "NULL",
}


# ---------------------------------------------------------------------------
# _clean helper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("hello", "hello", id="normal-string"),
        pytest.param("NULL", "", id="null-sentinel"),
        pytest.param("<okänd>", "", id="okand-sentinel"),
        pytest.param(None, "", id="none-value"),
        pytest.param("", "", id="empty-string"),
        pytest.param("  spaces  ", "spaces", id="strips-whitespace"),
        pytest.param(" NULL ", "", id="null-with-spaces"),
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# Basic fields
# ---------------------------------------------------------------------------


def test_full_row_basic_fields() -> None:
    record = FaltjagareRecord.from_csv_row(FULL_ROW)
    assert record.soldatnamn == "Modig"
    assert record.foernamn == "Anders"
    assert record.familjenamn == "Andersson"
    assert record.kompani == "Brunflo kompani"
    assert record.befattning == "Soldat"
    assert record.rotens_socken == "Brunflo"
    assert record.region == "Jämtland"
    assert record.from_tjaenst == "1710"
    assert record.till_tjaenst == "1718"
    assert record.foedelsedatum == "1685"
    assert record.foedelsesocken == "Brunflo"
    assert record.platsen_stupade == "Fredrikshald"
    assert record.doedsort == ""
    assert record.doedsdatum == "1718"
    assert record.oevrig_information == "Stupade vid belägringen av Fredrikshald"


# ---------------------------------------------------------------------------
# NULL and <okänd> sentinel → empty conversion
# ---------------------------------------------------------------------------


def test_null_converts_to_empty() -> None:
    record = FaltjagareRecord.from_csv_row(MINIMAL_ROW)
    assert record.familjenamn == ""
    assert record.foedelsedatum == ""
    assert record.platsen_stupade == ""
    assert record.doedsort == ""
    assert record.doedsdatum == ""


def test_okand_converts_to_empty() -> None:
    record = FaltjagareRecord.from_csv_row(MINIMAL_ROW)
    assert record.oevrig_information == ""


# ---------------------------------------------------------------------------
# Trailing-space column header
# ---------------------------------------------------------------------------


def test_trailing_space_in_column_header() -> None:
    """The CSV has 'Kommentar_startdatum ' with a trailing space — from_csv_row strips keys."""
    record = FaltjagareRecord.from_csv_row(FULL_ROW)
    # Should not raise; the trailing-space key is handled by .strip()
    assert record.soldatnamn == "Modig"


# ---------------------------------------------------------------------------
# searchable_text
# ---------------------------------------------------------------------------


def test_searchable_text_contains_key_fields() -> None:
    record = FaltjagareRecord.from_csv_row(FULL_ROW)
    text = record.searchable_text
    assert "Modig" in text
    assert "Anders" in text
    assert "Andersson" in text
    assert "Brunflo kompani" in text
    assert "Soldat" in text
    assert "Brunflo" in text
    assert "Jämtland" in text
    assert "Stupade vid belägringen av Fredrikshald" in text


def test_searchable_text_skips_empty_fields() -> None:
    record = FaltjagareRecord.from_csv_row(MINIMAL_ROW)
    text = record.searchable_text
    assert "NULL" not in text
    assert "<okänd>" not in text


def test_searchable_text_no_double_spaces() -> None:
    record = FaltjagareRecord.from_csv_row(FULL_ROW)
    text = record.searchable_text
    assert "  " not in text

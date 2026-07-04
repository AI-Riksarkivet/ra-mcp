"""Tests for SJ railway records Pydantic models."""

from __future__ import annotations

import pytest

from ra_mcp_sj_lib.models import JudaRecord, RitningRecord, _clean


# ---------------------------------------------------------------------------
# Test data: JUDA row
# ---------------------------------------------------------------------------

JUDA_ROW: dict[str, str] = {
    "FBPTYP": "J",
    "FBIDNR": "10001",
    "FBGVNR": "100",
    "FBTEXT": "ÄSPINGEN 1",
    "FBLAN": "14",
    "FBKOM": "1480",
    "FBFDBET": "NULL",
    "FBFDRGO": "NULL",
    "FBANM": "Stationshus med bostäder",
    "FBAGRKOD2": "Jernhusen",
    "FBBORT": "NULL",
    "FBUPVEM": "ADMIN",
    "FBUPDAT": "2005-01-15",
}

# ---------------------------------------------------------------------------
# Test data: FIRA row (with header)
# ---------------------------------------------------------------------------

FIRA_ROW: dict[str, str] = {
    "BNUM": "50001",
    "BLAD": "1",
    "AVD2": "A",
    "UAVD": "NULL",
    "RTYP2": "PLAN",
    "FORM2": "A1",
    "BDEL": "NULL",
    "DATM": "1920-05-15",
    "RITN": "R-50001",
    "BEN1": "GÖTEBORG N HUS 7",
    "BEN": "VVSSITPL",
    "SAKG": "SH",
    "SATS": "NULL",
    "DKOD": "GBG",
    "FILM": "F001",
    "AENDR": "NULL",
    "FOERV": "SJ",
    "UTLAA": "NULL",
}

# ---------------------------------------------------------------------------
# Test data: SIRA row (headerless, as list)
# ---------------------------------------------------------------------------

SIRA_VALUES: list[str] = [
    "60001",
    "1",
    "A",
    "NULL",
    "PLAN",
    "A1",
    "NULL",
    "1955-06-10",
    "R-60001",
    "KIRUNA STATION",
    "PLANLÖSNING",
    "SH",
    "NULL",
    "KNA",
    "F101",
    "NULL",
    "SJ",
    "NULL",
]


# ---------------------------------------------------------------------------
# _clean helper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("hello", "hello", id="normal-string"),
        pytest.param(None, "", id="none-value"),
        pytest.param("", "", id="empty-string"),
        pytest.param("  spaces  ", "spaces", id="strips-whitespace"),
        pytest.param("NULL", "", id="null-sentinel"),
        pytest.param('"quoted"', "quoted", id="strips-quotes"),
        pytest.param(' "NULL" ', "", id="quoted-null-also-cleaned"),
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# JudaRecord: basic fields
# ---------------------------------------------------------------------------


def test_juda_basic_fields() -> None:
    record = JudaRecord.from_csv_row(JUDA_ROW)
    assert record.fbptyp == "J"
    assert record.fbidnr == "10001"
    assert record.fbtext == "ÄSPINGEN 1"
    assert record.fblan == "14"
    assert record.fbkom == "1480"
    assert record.fbanm == "Stationshus med bostäder"
    assert record.fbagrkod2 == "Jernhusen"


def test_juda_null_sentinel_cleaned() -> None:
    record = JudaRecord.from_csv_row(JUDA_ROW)
    assert record.fbfdbet == ""
    assert record.fbfdrgo == ""
    assert record.fbbort == ""


def test_juda_searchable_text() -> None:
    record = JudaRecord.from_csv_row(JUDA_ROW)
    text = record.searchable_text
    assert "ÄSPINGEN 1" in text
    assert "Stationshus med bostäder" in text
    assert "Jernhusen" in text


def test_juda_searchable_text_skips_empty() -> None:
    row = {**JUDA_ROW, "FBANM": "NULL", "FBAGRKOD2": "NULL"}
    record = JudaRecord.from_csv_row(row)
    text = record.searchable_text
    assert "  " not in text
    assert text == "ÄSPINGEN 1"


# ---------------------------------------------------------------------------
# RitningRecord -- from_csv_row (FIRA with header)
# ---------------------------------------------------------------------------


def test_ritning_from_csv_row_basic() -> None:
    record = RitningRecord.from_csv_row(FIRA_ROW)
    assert record.bnum == "50001"
    assert record.blad == "1"
    assert record.rtyp2 == "PLAN"
    assert record.form2 == "A1"
    assert record.datm == "1920-05-15"
    assert record.ritn == "R-50001"
    assert record.ben1 == "GÖTEBORG N HUS 7"
    assert record.ben == "VVSSITPL"
    assert record.sakg == "SH"
    assert record.dkod == "GBG"


def test_ritning_null_sentinel_cleaned() -> None:
    record = RitningRecord.from_csv_row(FIRA_ROW)
    assert record.uavd == ""
    assert record.bdel == ""


def test_ritning_searchable_text() -> None:
    record = RitningRecord.from_csv_row(FIRA_ROW)
    text = record.searchable_text
    assert "GÖTEBORG N HUS 7" in text
    assert "VVSSITPL" in text
    assert "SH" in text
    assert "GBG" in text
    assert "R-50001" in text


# ---------------------------------------------------------------------------
# RitningRecord -- from_csv_list (SIRA headerless)
# ---------------------------------------------------------------------------


def test_ritning_from_csv_list_basic() -> None:
    record = RitningRecord.from_csv_list(SIRA_VALUES)
    assert record.bnum == "60001"
    assert record.blad == "1"
    assert record.datm == "1955-06-10"
    assert record.ritn == "R-60001"
    assert record.ben1 == "KIRUNA STATION"
    assert record.ben == "PLANLÖSNING"
    assert record.dkod == "KNA"


def test_ritning_from_csv_list_searchable_text() -> None:
    record = RitningRecord.from_csv_list(SIRA_VALUES)
    text = record.searchable_text
    assert "KIRUNA STATION" in text
    assert "PLANLÖSNING" in text

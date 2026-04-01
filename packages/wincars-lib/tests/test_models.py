"""Tests for Wincars Pydantic models."""

from __future__ import annotations

import pytest

from ra_mcp_wincars_lib.models import WincarsRecord, _clean


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

CAR_ROW: dict[str, str] = {
    "NREG": "X62045",
    "TYP": "PB",
    "FABRIKAT": "Volvo L 47513",
    "AAR": "1962",
    "FREG": "NULL",
    "MREG": "ABC123",
    "TREG": "NULL",
    "CNR": "123456",
    "MNR": "V62045",
    "STATUS": "A",
    "ANTAG": "1962-03-15",
    "AVREG": "1975-08-20",
    "HEMVIST": "Sundsvall",
    "ANM": "NULL",
    "ARKISKOD": "SE/RA/730144",
    "VOL": "3",
}

MC_ROW: dict[str, str] = {
    "NREG": "Y1234",
    "TYP": "MC",
    "FABRIKAT": "Husqvarna 250",
    "AAR": "1955",
    "FREG": "NULL",
    "MREG": "NULL",
    "TREG": "NULL",
    "CNR": "H55123",
    "MNR": "H55M01",
    "STATUS": "S",
    "ANTAG": "1955-06-01",
    "AVREG": "1968-11-30",
    "HEMVIST": "Umeå",
    "ANM": "Importerad från Norge",
    "ARKISKOD": "SE/RA/730145",
    "VOL": "5",
}

TRUCK_ROW_DASH_SENTINEL: dict[str, str] = {
    "NREG": "Z9876",
    "TYP": "LB",
    "FABRIKAT": "Scania-Vabis L 76",
    "AAR": "1970",
    "FREG": "X5000",
    "MREG": "NULL",
    "TREG": "NULL",
    "CNR": "SV70001",
    "MNR": "SV70E01",
    "STATUS": "NULL",
    "ANTAG": "1970-01-10",
    "AVREG": "- -",
    "HEMVIST": "Luleå",
    "ANM": "NULL",
    "ARKISKOD": "SE/RA/730146",
    "VOL": "7",
}


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
        pytest.param(" NULL ", "", id="null-sentinel-whitespace"),
        pytest.param("- -", "", id="dash-dash-sentinel"),
        pytest.param(" - - ", "", id="dash-dash-whitespace"),
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# WincarsRecord: basic fields (car)
# ---------------------------------------------------------------------------


def test_car_basic_fields() -> None:
    record = WincarsRecord.from_csv_row(CAR_ROW)
    assert record.nreg == "X62045"
    assert record.typ == "PB"
    assert record.fabrikat == "Volvo L 47513"
    assert record.aar == "1962"
    assert record.mreg == "ABC123"
    assert record.cnr == "123456"
    assert record.mnr == "V62045"
    assert record.status == "A"
    assert record.antag == "1962-03-15"
    assert record.avreg == "1975-08-20"
    assert record.hemvist == "Sundsvall"
    assert record.arkivkod == "SE/RA/730144"
    assert record.volym == "3"


def test_car_null_cleaned() -> None:
    record = WincarsRecord.from_csv_row(CAR_ROW)
    assert record.freg == ""
    assert record.treg == ""
    assert record.anm == ""


def test_car_typ_display() -> None:
    record = WincarsRecord.from_csv_row(CAR_ROW)
    assert record.typ_display == "Personbil"


# ---------------------------------------------------------------------------
# Motorcycle fields
# ---------------------------------------------------------------------------


def test_mc_basic_fields() -> None:
    record = WincarsRecord.from_csv_row(MC_ROW)
    assert record.nreg == "Y1234"
    assert record.typ == "MC"
    assert record.fabrikat == "Husqvarna 250"
    assert record.status == "S"
    assert record.anm == "Importerad från Norge"


def test_mc_typ_display() -> None:
    record = WincarsRecord.from_csv_row(MC_ROW)
    assert record.typ_display == "Motorcykel"


# ---------------------------------------------------------------------------
# WincarsRecord: truck with dash-dash sentinel
# ---------------------------------------------------------------------------


def test_truck_dash_dash_sentinel() -> None:
    record = WincarsRecord.from_csv_row(TRUCK_ROW_DASH_SENTINEL)
    assert record.avreg == ""
    assert record.status == ""


def test_truck_freg_preserved() -> None:
    record = WincarsRecord.from_csv_row(TRUCK_ROW_DASH_SENTINEL)
    assert record.freg == "X5000"


def test_truck_typ_display() -> None:
    record = WincarsRecord.from_csv_row(TRUCK_ROW_DASH_SENTINEL)
    assert record.typ_display == "Lastbil"


# ---------------------------------------------------------------------------
# searchable_text
# ---------------------------------------------------------------------------


def test_searchable_text_includes_key_fields() -> None:
    record = WincarsRecord.from_csv_row(CAR_ROW)
    text = record.searchable_text
    assert "X62045" in text
    assert "Volvo L 47513" in text
    assert "Sundsvall" in text
    assert "ABC123" in text


def test_searchable_text_skips_empty() -> None:
    record = WincarsRecord.from_csv_row(CAR_ROW)
    text = record.searchable_text
    assert "  " not in text


def test_searchable_text_includes_anm_when_present() -> None:
    record = WincarsRecord.from_csv_row(MC_ROW)
    text = record.searchable_text
    assert "Importerad från Norge" in text


# ---------------------------------------------------------------------------
# typ_display: all known types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "typ_code,expected",
    [
        pytest.param("PB", "Personbil", id="car"),
        pytest.param("MC", "Motorcykel", id="motorcycle"),
        pytest.param("LB", "Lastbil", id="truck"),
        pytest.param("SL", "Släpvagn", id="trailer"),
        pytest.param("TR", "Traktor", id="tractor"),
        pytest.param("BS", "Buss", id="bus"),
    ],
)
def test_typ_display_all_types(typ_code: str, expected: str) -> None:
    record = WincarsRecord(typ=typ_code)
    assert record.typ_display == expected


def test_typ_display_unknown_passthrough() -> None:
    record = WincarsRecord(typ="XX")
    assert record.typ_display == "XX"

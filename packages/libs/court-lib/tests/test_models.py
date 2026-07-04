"""Tests for court records Pydantic models."""

from __future__ import annotations

import pytest

from ra_mcp_court_lib.models import DomboksregisterRecord, MedelstadRecord, _clean


# ---------------------------------------------------------------------------
# Test data: Domboksregister Person row (quoted fields)
# ---------------------------------------------------------------------------

PERSON_ROW: dict[str, str] = {
    "Id": "1",
    "Nr": "1",
    "Roll": "Kärande",
    "Kategori": "M",
    "Titel": "Bonde",
    "Fnamn": "Anders",
    "Enamn": "Persson",
    "Socken": "Kinnevald",
    "Plats": "Torp",
    "Anteckning": "Stämde om skuld",
    "ParagrafId": "P001",
}

PARAGRAF_MAP: dict[str, dict[str, str]] = {
    "P001": {"Datum": "1650-03-12", "Arende": "Skuld och fordran"},
    "P002": {"Datum": "1650-03-12", "Arende": "Arvstvist"},
}

# ---------------------------------------------------------------------------
# Test data: Medelstad personposter row
# ---------------------------------------------------------------------------

MEDELSTAD_ROW: dict[str, str] = {
    "Löpnr": "1",
    "FEnamnTitel": "Anders Persson bonde",
    "PlatsFörsamling": "Torp Listerby",
    "Norm_förnamn": "Anders",
    "Normefternamn": "Persson",
    "Norm_titel": "Bonde",
    "Normplats": "Torp",
    "Norm_församling": "Listerby",
    "Ting_dag": "1690-03-10",
    "Ting_typ": "Ordinarie ting",
    "Mål_nr": "1",
    "Mål_typ": "Skuld",
}

MAAL_MAP: dict[str, str] = {
    "1": "Anders Persson stämde Nils Jonsson för en skuld på 10 daler silvermynt.",
    "2": "Nils Jonsson nekade till skulden.",
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
        pytest.param('"quoted"', "quoted", id="strips-quotes"),
        pytest.param(' "quoted with spaces" ', "quoted with spaces", id="strips-both"),
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# DomboksregisterRecord: basic fields
# ---------------------------------------------------------------------------


def test_domboksregister_basic_fields() -> None:
    record = DomboksregisterRecord.from_csv_row(PERSON_ROW, PARAGRAF_MAP)
    assert record.id == 1
    assert record.fnamn == "Anders"
    assert record.enamn == "Persson"
    assert record.roll == "Kärande"
    assert record.kategori == "M"
    assert record.titel == "Bonde"
    assert record.socken == "Kinnevald"
    assert record.plats == "Torp"
    assert record.anteckning == "Stämde om skuld"


def test_domboksregister_paragraf_join() -> None:
    record = DomboksregisterRecord.from_csv_row(PERSON_ROW, PARAGRAF_MAP)
    assert record.datum == "1650-03-12"
    assert record.arende == "Skuld och fordran"


def test_domboksregister_without_paragraf_map() -> None:
    record = DomboksregisterRecord.from_csv_row(PERSON_ROW)
    assert record.datum == ""
    assert record.arende == ""


def test_domboksregister_missing_paragraf_id() -> None:
    record = DomboksregisterRecord.from_csv_row(PERSON_ROW, {"P999": {"Datum": "x", "Arende": "y"}})
    assert record.datum == ""
    assert record.arende == ""


# ---------------------------------------------------------------------------
# Domboksregister searchable text
# ---------------------------------------------------------------------------


def test_domboksregister_searchable_text() -> None:
    record = DomboksregisterRecord.from_csv_row(PERSON_ROW, PARAGRAF_MAP)
    text = record.searchable_text
    assert "Anders" in text
    assert "Persson" in text
    assert "Bonde" in text
    assert "Kinnevald" in text
    assert "Torp" in text
    assert "Skuld och fordran" in text


def test_domboksregister_searchable_text_skips_empty() -> None:
    row = {**PERSON_ROW, "Titel": "", "Plats": ""}
    record = DomboksregisterRecord.from_csv_row(row)
    text = record.searchable_text
    assert "  " not in text


# ---------------------------------------------------------------------------
# MedelstadRecord: basic fields
# ---------------------------------------------------------------------------


def test_medelstad_basic_fields() -> None:
    record = MedelstadRecord.from_csv_row(MEDELSTAD_ROW, MAAL_MAP)
    assert record.lopnr == 1
    assert record.norm_fornamn == "Anders"
    assert record.norm_efternamn == "Persson"
    assert record.norm_titel == "Bonde"
    assert record.norm_plats == "Torp"
    assert record.norm_forsamling == "Listerby"
    assert record.ting_dag == "1690-03-10"
    assert record.ting_typ == "Ordinarie ting"
    assert record.mal_nr == "1"
    assert record.mal_typ == "Skuld"


def test_medelstad_maal_join() -> None:
    record = MedelstadRecord.from_csv_row(MEDELSTAD_ROW, MAAL_MAP)
    assert "Anders Persson stämde Nils Jonsson" in record.mal_referat


def test_medelstad_without_maal_map() -> None:
    record = MedelstadRecord.from_csv_row(MEDELSTAD_ROW)
    assert record.mal_referat == ""


def test_medelstad_missing_lopnr_in_maal() -> None:
    record = MedelstadRecord.from_csv_row(MEDELSTAD_ROW, {"999": "No match"})
    assert record.mal_referat == ""


# ---------------------------------------------------------------------------
# Medelstad searchable text
# ---------------------------------------------------------------------------


def test_medelstad_searchable_text() -> None:
    record = MedelstadRecord.from_csv_row(MEDELSTAD_ROW, MAAL_MAP)
    text = record.searchable_text
    assert "Anders" in text
    assert "Persson" in text
    assert "Bonde" in text
    assert "Listerby" in text
    assert "Skuld" in text
    assert "stämde Nils Jonsson" in text


def test_medelstad_searchable_text_skips_empty() -> None:
    row = {**MEDELSTAD_ROW, "Norm_titel": "", "Normplats": ""}
    record = MedelstadRecord.from_csv_row(row)
    text = record.searchable_text
    assert "  " not in text

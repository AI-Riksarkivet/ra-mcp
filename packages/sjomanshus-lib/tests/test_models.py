"""Tests for Sjömanshus Pydantic models."""

from __future__ import annotations

import pytest

from ra_mcp_sjomanshus_lib.models import LiggareRecord, MatrikelRecord, _clean


# ---------------------------------------------------------------------------
# Test data: Liggare row (Jonas Pettersson, matros)
# ---------------------------------------------------------------------------

LIGGARE_ROW: dict[str, str] = {
    "ID": "1",
    "Sid": "100",
    "Foernamn": "Jonas",
    "Efternamn1": "Pettersson",
    "Efternamn2": "",
    "Foedelsedat": "1825-03-15",
    "Aalder": "30",
    "Foedelseplats": "Karlskrona",
    "Foedelsefoers": "Karlskrona stadsförsamling",
    "FSCBkod": "0123",
    "Hemplats": "Karlskrona",
    "Hemfoers": "Karlskrona stadsförsamling",
    "HSCBkod": "0123",
    "Civilstaand": "Ogift",
    "Sjoemanshus": "Karlskrona",
    "Inskrivnr": "1234",
    "Hyra_Loen": "15",
    "Valuta": "Riksdaler",
    "Betaltid": "Månad",
    "Befattning_Yrke": "Matros",
    "Befattningskod": "01",
    "Paamoenstort": "Karlskrona",
    "Paamoenstkod": "",
    "Paamoenstdat": "1855-04-10",
    "Avmoenstort": "Göteborg",
    "Avmoenstkod": "",
    "Avmoenstdat": "1855-09-20",
    "Orsak": "Hemförlovad",
    "Anm": "",
    "Fartyg": "Briggen Hoppet",
    "Typ": "Brigg",
    "Regnr": "456",
    "Svaara_Laester": "",
    "Nylaester": "120",
    "Registerton": "85",
    "Hemmahamn": "Karlskrona",
    "Destination": "Medelhavet",
    "Redare": "J. Andersson",
    "Kapten": "C. Lindberg",
    "Oevrigt": "Första resan",
    "Volym": "Vol 1",
    "Sida": "23",
    "Arkiv": "Karlskrona sjömanshus",
    "Arkisnr": "SE/KrA/0123",
}

# ---------------------------------------------------------------------------
# Test data: Liggare row with empty fields
# ---------------------------------------------------------------------------

LIGGARE_EMPTY_ROW: dict[str, str] = {
    "ID": "4",
    "Sid": "103",
    "Foernamn": "Anders",
    "Efternamn1": "Lundgren",
    "Efternamn2": "",
    "Foedelsedat": "1828-09-30",
    "Aalder": "27",
    "Foedelseplats": "Malmö",
    "Foedelsefoers": "Malmö stadsförsamling",
    "FSCBkod": "1012",
    "Hemplats": "Malmö",
    "Hemfoers": "Malmö stadsförsamling",
    "HSCBkod": "1012",
    "Civilstaand": "Gift",
    "Sjoemanshus": "Malmö",
    "Inskrivnr": "4567",
    "Hyra_Loen": "12",
    "Valuta": "Riksdaler",
    "Betaltid": "Månad",
    "Befattning_Yrke": "Kock",
    "Befattningskod": "04",
    "Paamoenstort": "Malmö",
    "Paamoenstkod": "",
    "Paamoenstdat": "1855-06-15",
    "Avmoenstort": "Hamburg",
    "Avmoenstkod": "",
    "Avmoenstdat": "1856-01-10",
    "Orsak": "",
    "Anm": "",
    "Fartyg": "Briggen Svea",
    "Typ": "Brigg",
    "Regnr": "567",
    "Svaara_Laester": "",
    "Nylaester": "110",
    "Registerton": "80",
    "Hemmahamn": "Malmö",
    "Destination": "Östersjön",
    "Redare": "L. Svensson",
    "Kapten": "O. Berglund",
    "Oevrigt": "",
    "Volym": "Vol 4",
    "Sida": "89",
    "Arkiv": "Malmö sjömanshus",
    "Arkisnr": "SE/MSA/1012",
}

# ---------------------------------------------------------------------------
# Test data: Matrikel row (Jonas Pettersson)
# ---------------------------------------------------------------------------

MATRIKEL_ROW: dict[str, str] = {
    "ID": "1",
    "Sid": "200",
    "Foernamn": "Jonas",
    "Efternamn1": "Pettersson",
    "Efternamn2": "",
    "Foedelsedat": "1825-03-15",
    "Foedelseplats": "Karlskrona",
    "Foedelsefoers": "Karlskrona stadsförsamling",
    "FSCBkod": "0123",
    "Hemplats": "Karlskrona",
    "Hemfoers": "Karlskrona stadsförsamling",
    "HSCBkod": "0123",
    "Nyhemplats": "",
    "Nyhemfoers": "",
    "NyHSCBkod": "",
    "Flyttdat": "",
    "Far": "Per Pettersson",
    "Mor": "Anna Larsdotter",
    "Sjoemanshus": "Karlskrona",
    "Inskrivnr": "1234",
    "Inskrivdat": "1840-05-01",
    "Avfoerdort": "",
    "Avfoerddat": "",
    "Orsak": "",
    "Anm": "",
    "Nyttsjoehus": "",
    "Nyttinskrivnr": "",
    "Oevrigt": "",
    "Volym": "Vol 1",
    "Sida": "10",
    "Arkiv": "Karlskrona sjömanshus",
    "Arkisnr": "SE/KrA/0123",
}

# ---------------------------------------------------------------------------
# Test data: Matrikel row with more fields
# ---------------------------------------------------------------------------

MATRIKEL_FULL_ROW: dict[str, str] = {
    "ID": "2",
    "Sid": "201",
    "Foernamn": "Nils",
    "Efternamn1": "Andersson",
    "Efternamn2": "Svensson",
    "Foedelsedat": "1830-06-22",
    "Foedelseplats": "Landskrona",
    "Foedelsefoers": "Landskrona stadsförsamling",
    "FSCBkod": "0456",
    "Hemplats": "Landskrona",
    "Hemfoers": "Landskrona stadsförsamling",
    "HSCBkod": "0456",
    "Nyhemplats": "",
    "Nyhemfoers": "",
    "NyHSCBkod": "",
    "Flyttdat": "",
    "Far": "Anders Nilsson",
    "Mor": "Maja Svensdotter",
    "Sjoemanshus": "Landskrona",
    "Inskrivnr": "2345",
    "Inskrivdat": "1845-08-15",
    "Avfoerdort": "Göteborg",
    "Avfoerddat": "1860-03-01",
    "Orsak": "Flyttad",
    "Anm": "Flyttad till Göteborg",
    "Nyttsjoehus": "Göteborg",
    "Nyttinskrivnr": "6789",
    "Oevrigt": "Omregistrerad",
    "Volym": "Vol 2",
    "Sida": "22",
    "Arkiv": "Landskrona sjömanshus",
    "Arkisnr": "SE/KrA/0456",
}


# ---------------------------------------------------------------------------
# _clean helper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("hello", "hello", id="normal-string"),
        pytest.param("NULL", "", id="null-sentinel"),
        pytest.param(None, "", id="none-value"),
        pytest.param("", "", id="empty-string"),
        pytest.param("  spaces  ", "spaces", id="strips-whitespace"),
        pytest.param("NULL ", "", id="null-with-trailing-space"),
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# LiggareRecord: basic fields
# ---------------------------------------------------------------------------


def test_liggare_basic_fields() -> None:
    record = LiggareRecord.from_csv_row(LIGGARE_ROW)
    assert record.id == 1
    assert record.foernamn == "Jonas"
    assert record.efternamn1 == "Pettersson"
    assert record.efternamn2 == ""
    assert record.foedelsedat == "1825-03-15"
    assert record.aalder == "30"
    assert record.civilstaand == "Ogift"
    assert record.sjoemanshus == "Karlskrona"
    assert record.inskrivnr == "1234"


def test_liggare_voyage_fields() -> None:
    record = LiggareRecord.from_csv_row(LIGGARE_ROW)
    assert record.befattning_yrke == "Matros"
    assert record.paamoenstort == "Karlskrona"
    assert record.paamoenstdat == "1855-04-10"
    assert record.avmoenstort == "Göteborg"
    assert record.avmoenstdat == "1855-09-20"
    assert record.orsak == "Hemförlovad"


def test_liggare_ship_fields() -> None:
    record = LiggareRecord.from_csv_row(LIGGARE_ROW)
    assert record.fartyg == "Briggen Hoppet"
    assert record.typ == "Brigg"
    assert record.hemmahamn == "Karlskrona"
    assert record.destination == "Medelhavet"
    assert record.redare == "J. Andersson"
    assert record.kapten == "C. Lindberg"


def test_liggare_archive_fields() -> None:
    record = LiggareRecord.from_csv_row(LIGGARE_ROW)
    assert record.volym == "Vol 1"
    assert record.sida == "23"
    assert record.arkiv == "Karlskrona sjömanshus"
    assert record.arkivnr == "SE/KrA/0123"


def test_liggare_empty_fields() -> None:
    record = LiggareRecord.from_csv_row(LIGGARE_EMPTY_ROW)
    assert record.orsak == ""
    assert record.anm == ""
    assert record.oevrigt == ""


# ---------------------------------------------------------------------------
# Liggare searchable text
# ---------------------------------------------------------------------------


def test_liggare_searchable_text_contains_key_fields() -> None:
    record = LiggareRecord.from_csv_row(LIGGARE_ROW)
    text = record.searchable_text
    assert "Jonas" in text
    assert "Pettersson" in text
    assert "Matros" in text
    assert "Briggen Hoppet" in text
    assert "Karlskrona" in text
    assert "Medelhavet" in text
    assert "J. Andersson" in text
    assert "C. Lindberg" in text
    assert "Första resan" in text


def test_liggare_searchable_text_skips_empty_fields() -> None:
    record = LiggareRecord.from_csv_row(LIGGARE_EMPTY_ROW)
    text = record.searchable_text
    assert "  " not in text


# ---------------------------------------------------------------------------
# MatrikelRecord: basic fields
# ---------------------------------------------------------------------------


def test_matrikel_basic_fields() -> None:
    record = MatrikelRecord.from_csv_row(MATRIKEL_ROW)
    assert record.id == 1
    assert record.foernamn == "Jonas"
    assert record.efternamn1 == "Pettersson"
    assert record.foedelsedat == "1825-03-15"
    assert record.sjoemanshus == "Karlskrona"
    assert record.inskrivnr == "1234"
    assert record.inskrivdat == "1840-05-01"
    assert record.far == "Per Pettersson"
    assert record.mor == "Anna Larsdotter"


def test_matrikel_full_fields() -> None:
    record = MatrikelRecord.from_csv_row(MATRIKEL_FULL_ROW)
    assert record.id == 2
    assert record.efternamn2 == "Svensson"
    assert record.avfoerdort == "Göteborg"
    assert record.avfoerddat == "1860-03-01"
    assert record.orsak == "Flyttad"
    assert record.anm == "Flyttad till Göteborg"
    assert record.oevrigt == "Omregistrerad"


def test_matrikel_archive_fields() -> None:
    record = MatrikelRecord.from_csv_row(MATRIKEL_ROW)
    assert record.volym == "Vol 1"
    assert record.sida == "10"
    assert record.arkiv == "Karlskrona sjömanshus"
    assert record.arkivnr == "SE/KrA/0123"


# ---------------------------------------------------------------------------
# Matrikel searchable text
# ---------------------------------------------------------------------------


def test_matrikel_searchable_text_contains_key_fields() -> None:
    record = MatrikelRecord.from_csv_row(MATRIKEL_FULL_ROW)
    text = record.searchable_text
    assert "Nils" in text
    assert "Andersson" in text
    assert "Svensson" in text
    assert "Anders Nilsson" in text
    assert "Maja Svensdotter" in text
    assert "Landskrona stadsförsamling" in text
    assert "Omregistrerad" in text


def test_matrikel_searchable_text_skips_empty_fields() -> None:
    record = MatrikelRecord.from_csv_row(MATRIKEL_ROW)
    text = record.searchable_text
    assert "  " not in text
    # Should have foernamn + efternamn1 + far + mor + foedelsefoers + hemfoers
    assert "Jonas" in text
    assert "Per Pettersson" in text
    assert "Anna Larsdotter" in text

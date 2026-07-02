"""Tests for Specialsök Pydantic models."""

from __future__ import annotations

import pytest

from ra_mcp_specialsok_lib.models import (
    FangrullorRecord,
    FlygvapenRecord,
    KurhusetRecord,
    PressRecord,
    VideoRecord,
    _clean,
)


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
        pytest.param("Borttaget", "", id="sentinel-borttaget"),
        pytest.param("NULL", "", id="sentinel-null"),
        pytest.param("null", "", id="sentinel-null-lower"),
        pytest.param(' "quoted with spaces" ', "quoted with spaces", id="strips-both"),
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# FlygvapenRecord
# ---------------------------------------------------------------------------

FLYGVAPEN_ROW: dict[str, str] = {
    "Datum": "1960-07-22",
    "Förband": "F10",
    "Förband klartext": "Ängelholms flygflottilj",
    "FplTyp": "J 35A",
    "FplNr": "35102",
    "MotorTyp": "RM6A",
    "Haveri": "Totalhavererat",
    "BesAnt": "1",
    "AntOmk": "0",
    "Grad1": "Kapten",
    "Fask1": "Jaktpilot",
    "Sammanfattning": "Draken kraschade vid provflygning",
    "Havplats": "Ängelholm",
    "Klassning": "B",
}


def test_flygvapen_basic_fields() -> None:
    rec = FlygvapenRecord.from_csv_row(FLYGVAPEN_ROW)
    assert rec.datum == "1960-07-22"
    assert rec.fpl_typ == "J 35A"
    assert rec.forband_klartext == "Ängelholms flygflottilj"
    assert rec.havplats == "Ängelholm"
    assert rec.sammanfattning == "Draken kraschade vid provflygning"


def test_flygvapen_searchable_text() -> None:
    rec = FlygvapenRecord.from_csv_row(FLYGVAPEN_ROW)
    text = rec.searchable_text
    assert "J 35A" in text
    assert "Ängelholms flygflottilj" in text
    assert "Draken kraschade" in text
    assert "Ängelholm" in text


# ---------------------------------------------------------------------------
# FangrullorRecord
# ---------------------------------------------------------------------------

FANGRULLOR_ROW: dict[str, str] = {
    "Efternamn": "Andersson",
    "Fornamn": "Erik",
    "Alder": "35",
    "Hemort": "Ås",
    "Brott": "Stöld",
    "Nummer": "101",
    "Ar": "1845",
}


def test_fangrullor_basic_fields() -> None:
    rec = FangrullorRecord.from_csv_row(FANGRULLOR_ROW)
    assert rec.efternamn == "Andersson"
    assert rec.fornamn == "Erik"
    assert rec.hemort == "Ås"
    assert rec.brott == "Stöld"
    assert rec.ar == "1845"


def test_fangrullor_searchable_text() -> None:
    rec = FangrullorRecord.from_csv_row(FANGRULLOR_ROW)
    text = rec.searchable_text
    assert "Andersson" in text
    assert "Erik" in text
    assert "Ås" in text
    assert "Stöld" in text


# ---------------------------------------------------------------------------
# KurhusetRecord
# ---------------------------------------------------------------------------

KURHUSET_ROW: dict[str, str] = {
    "NUMMER": "1",
    "INSKRIVNINGSDATUM": "1820-03-15",
    "FÖRNAMN": "Maria",
    "EFTERNAMN": "Andersdotter",
    "ÅLDER": "25",
    "TITEL": "Piga",
    "FAMILJ": "Ogift",
    "BY": "Nöbbelöv",
    "SOCKEN": "Barsebäck",
    "SJUKDOM": "Syfilis",
    "SJUKDOMSBESKRIVNING": "Primära symptom",
    "SJUKDOMSBEHANDLING": "Kvicksilverbehandling",
    "UTSKRIVNINGSDATUM": "1820-06-10",
    "UTSKRIVNINGSSTATUS": "Botad",
    "VÅRDTID": "87",
    "ANMÄRKNING": "",
}


def test_kurhuset_basic_fields() -> None:
    rec = KurhusetRecord.from_csv_row(KURHUSET_ROW)
    assert rec.fornamn == "Maria"
    assert rec.efternamn == "Andersdotter"
    assert rec.sjukdom == "Syfilis"
    assert rec.sjukdomsbehandling == "Kvicksilverbehandling"
    assert rec.utskrivningsstatus == "Botad"


def test_kurhuset_searchable_text() -> None:
    rec = KurhusetRecord.from_csv_row(KURHUSET_ROW)
    text = rec.searchable_text
    assert "Maria" in text
    assert "Andersdotter" in text
    assert "Syfilis" in text
    assert "Barsebäck" in text


# ---------------------------------------------------------------------------
# PressRecord
# ---------------------------------------------------------------------------

PRESS_ROW: dict[str, str] = {
    "V_RA_NR": "RA001",
    "DATUM": "1995-03-15",
    "AAR": "1995",
    "Titel": "EU-medlemskap",
    "INNEHAALL": "Sverige och EU-samarbetet diskuterades",
    "ARKIVBILDARE_SAMLING": "Statsrådsberedningen",
    "ANMAERKNING": "",
}


def test_press_basic_fields() -> None:
    rec = PressRecord.from_csv_row(PRESS_ROW)
    assert rec.titel == "EU-medlemskap"
    assert rec.aar == "1995"
    assert rec.innehaall == "Sverige och EU-samarbetet diskuterades"


def test_press_searchable_text() -> None:
    rec = PressRecord.from_csv_row(PRESS_ROW)
    text = rec.searchable_text
    assert "EU-medlemskap" in text
    assert "EU-samarbetet" in text


# ---------------------------------------------------------------------------
# VideoRecord
# ---------------------------------------------------------------------------

VIDEO_ROW: dict[str, str] = {
    "Reg_nr": "V001",
    "Laen": "Stockholms län",
    "Kommun": "Stockholm",
    "Butiksnamn": "Video King",
    "Firmanamn": "Video King AB",
    "Aktiv": "Ja",
    "Besoeksadress": "Kungsgatan 10",
    "Ort": "Stockholm",
    "Landsdel": "Svealand",
}


def test_video_basic_fields() -> None:
    rec = VideoRecord.from_csv_row(VIDEO_ROW)
    assert rec.butiksnamn == "Video King"
    assert rec.firmanamn == "Video King AB"
    assert rec.kommun == "Stockholm"


def test_video_sentinel_cleaning() -> None:
    row = {**VIDEO_ROW, "Firmanamn": "Borttaget", "Ort": "NULL"}
    rec = VideoRecord.from_csv_row(row)
    assert rec.firmanamn == ""
    assert rec.ort == ""


def test_video_searchable_text() -> None:
    rec = VideoRecord.from_csv_row(VIDEO_ROW)
    text = rec.searchable_text
    assert "Video King" in text
    assert "Stockholm" in text
    assert "Stockholms län" in text


def test_video_searchable_text_skips_sentinels() -> None:
    row = {**VIDEO_ROW, "Firmanamn": "Borttaget"}
    rec = VideoRecord.from_csv_row(row)
    text = rec.searchable_text
    assert "Borttaget" not in text

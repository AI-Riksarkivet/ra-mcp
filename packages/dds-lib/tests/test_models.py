"""Tests for DDS Pydantic models."""

from __future__ import annotations

import pytest

from ra_mcp_dds_lib.models import DodaRecord, FodelseRecord, VigselRecord, _clean


# ---------------------------------------------------------------------------
# Test data: Födelse row
# ---------------------------------------------------------------------------

FODELSE_ROW: dict[str, str] = {
    "Postid": "1001",
    "Forsamling": "Klara",
    "Lan": "Stockholm",
    "Datum": "1842-03-15",
    "Fornamn": "Anna Maria",
    "Kon": "K",
    "Far_fornamn": "Johan",
    "Far_efternamn": "Lindberg",
    "Far_yrke": "Skomakare",
    "Far_ort": "Stockholm",
    "Mor_fornamn": "Brita",
    "Mor_efternamn": "Lindberg",
    "Mor_yrke": "NULL",
    "Fodelseort": "Stockholm",
    "Dopvittne": "Per Andersson, Maria Svensson",
    "Anm": "NULL",
    "Referenskod": "SE/SSA/0012",
    "Volym": "C:5",
    "BildID": "A0012345",
}

FODELSE_ROW_OAKTA: dict[str, str] = {
    "Postid": "1003",
    "Forsamling": "Hedvig Eleonora",
    "Lan": "Stockholm",
    "Datum": "1845-01-10",
    "Fornamn": "Eva Charlotta",
    "Kon": "K",
    "Far_fornamn": "NULL",
    "Far_efternamn": "NULL",
    "Far_yrke": "NULL",
    "Far_ort": "NULL",
    "Mor_fornamn": "Lovisa",
    "Mor_efternamn": "Eriksson",
    "Mor_yrke": "Piga",
    "Fodelseort": "Hedvig Eleonora",
    "Dopvittne": "Anna Nilsson",
    "Anm": "O\u00e4kta barn",
    "Referenskod": "SE/SSA/0020",
    "Volym": "C:3",
    "BildID": "A0012347",
}

# ---------------------------------------------------------------------------
# Test data: Döda row
# ---------------------------------------------------------------------------

DODA_ROW: dict[str, str] = {
    "PostID": "2001",
    "Forsamling": "Klara",
    "Lan": "Stockholm",
    "Datum": "1855-02-14",
    "Fornamn": "Anna",
    "Efternamn": "Lindberg",
    "Yrke": "NULL",
    "Hemort": "Klara",
    "Kon": "K",
    "Civilstand": "Gift",
    "Alder": "45",
    "Dodsorsak": "Lungsot",
    "Dodsorsak_klassificerat": "Tuberkulos",
    "Anhorig_fornamn": "Johan",
    "Anhorig_efternamn": "Lindberg",
    "Anhorig_yrke": "Skomakare",
    "Anhorig_relation": "Man",
    "Anm": "NULL",
    "Referenskod": "SE/SSA/0012",
    "Volym": "F:3",
    "BildID": "B0023456",
}

# ---------------------------------------------------------------------------
# Test data: Vigsel row
# ---------------------------------------------------------------------------

VIGSEL_ROW: dict[str, str] = {
    "Postid": "3001",
    "Forsamling": "Klara",
    "Lan": "Stockholm",
    "Datum": "1850-06-12",
    "Brudgum_fornamn": "Johan",
    "Brudgum_efternamn": "Lindberg",
    "Brudgum_yrke": "Skomakare",
    "Brudgum_hemort": "Klara",
    "Brudgum_civilstand": "Ogift",
    "Brudgum_alder": "28",
    "Brud_fornamn": "Anna Maria",
    "Brud_efternamn": "Svensson",
    "Brud_yrke": "Piga",
    "Brud_hemort": "Klara",
    "Brud_Alder": "22",
    "Anm": "NULL",
    "Referenskod": "SE/SSA/0012",
    "Volym": "E:2",
    "BildID": "C0034567",
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
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# FodelseRecord: basic fields
# ---------------------------------------------------------------------------


def test_fodelse_basic_fields() -> None:
    record = FodelseRecord.from_csv_row(FODELSE_ROW)
    assert record.postid == "1001"
    assert record.forsamling == "Klara"
    assert record.lan == "Stockholm"
    assert record.datum == "1842-03-15"
    assert record.fornamn == "Anna Maria"
    assert record.kon == "K"
    assert record.far_fornamn == "Johan"
    assert record.far_efternamn == "Lindberg"
    assert record.far_yrke == "Skomakare"
    assert record.far_ort == "Stockholm"
    assert record.mor_fornamn == "Brita"
    assert record.mor_efternamn == "Lindberg"
    assert record.referenskod == "SE/SSA/0012"
    assert record.bild_id == "A0012345"


def test_fodelse_null_cleaned() -> None:
    record = FodelseRecord.from_csv_row(FODELSE_ROW)
    assert record.mor_yrke == ""
    assert record.anm == ""


def test_fodelse_oakta_null_father() -> None:
    record = FodelseRecord.from_csv_row(FODELSE_ROW_OAKTA)
    assert record.far_fornamn == ""
    assert record.far_efternamn == ""
    assert record.far_yrke == ""
    assert record.anm == "O\u00e4kta barn"


def test_fodelse_searchable_text() -> None:
    record = FodelseRecord.from_csv_row(FODELSE_ROW)
    text = record.searchable_text
    assert "Anna Maria" in text
    assert "Johan" in text
    assert "Lindberg" in text
    assert "Skomakare" in text
    assert "Klara" in text
    assert "Stockholm" in text


def test_fodelse_searchable_text_skips_empty() -> None:
    record = FodelseRecord.from_csv_row(FODELSE_ROW_OAKTA)
    text = record.searchable_text
    assert "  " not in text


# ---------------------------------------------------------------------------
# DodaRecord: basic fields
# ---------------------------------------------------------------------------


def test_doda_basic_fields() -> None:
    record = DodaRecord.from_csv_row(DODA_ROW)
    assert record.postid == "2001"
    assert record.forsamling == "Klara"
    assert record.fornamn == "Anna"
    assert record.efternamn == "Lindberg"
    assert record.civilstand == "Gift"
    assert record.alder == "45"
    assert record.dodsorsak == "Lungsot"
    assert record.dodsorsak_klassificerat == "Tuberkulos"
    assert record.anhorig_fornamn == "Johan"
    assert record.anhorig_efternamn == "Lindberg"
    assert record.anhorig_relation == "Man"


def test_doda_null_cleaned() -> None:
    record = DodaRecord.from_csv_row(DODA_ROW)
    assert record.yrke == ""
    assert record.anm == ""


def test_doda_searchable_text() -> None:
    record = DodaRecord.from_csv_row(DODA_ROW)
    text = record.searchable_text
    assert "Anna" in text
    assert "Lindberg" in text
    assert "Lungsot" in text
    assert "Tuberkulos" in text
    assert "Johan" in text
    assert "Klara" in text


# ---------------------------------------------------------------------------
# VigselRecord: basic fields
# ---------------------------------------------------------------------------


def test_vigsel_basic_fields() -> None:
    record = VigselRecord.from_csv_row(VIGSEL_ROW)
    assert record.postid == "3001"
    assert record.forsamling == "Klara"
    assert record.datum == "1850-06-12"
    assert record.brudgum_fornamn == "Johan"
    assert record.brudgum_efternamn == "Lindberg"
    assert record.brudgum_yrke == "Skomakare"
    assert record.brud_fornamn == "Anna Maria"
    assert record.brud_efternamn == "Svensson"
    assert record.brud_yrke == "Piga"
    assert record.brud_alder == "22"


def test_vigsel_null_cleaned() -> None:
    record = VigselRecord.from_csv_row(VIGSEL_ROW)
    assert record.anm == ""


def test_vigsel_searchable_text() -> None:
    record = VigselRecord.from_csv_row(VIGSEL_ROW)
    text = record.searchable_text
    assert "Johan" in text
    assert "Lindberg" in text
    assert "Skomakare" in text
    assert "Anna Maria" in text
    assert "Svensson" in text
    assert "Piga" in text
    assert "Klara" in text


def test_vigsel_searchable_text_skips_empty() -> None:
    record = VigselRecord.from_csv_row(VIGSEL_ROW)
    text = record.searchable_text
    assert "  " not in text

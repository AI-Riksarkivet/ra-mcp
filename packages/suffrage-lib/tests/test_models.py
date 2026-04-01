"""Tests for Suffrage Pydantic models."""

from __future__ import annotations

import pytest

from ra_mcp_suffrage_lib.models import FKPRRecord, RostrattRecord, _clean


# ---------------------------------------------------------------------------
# Test data: Rösträtt row (Anna Svensson)
# ---------------------------------------------------------------------------

ROSTRATT_ROW: dict[str, str] = {
    "Volymens_l\u00e4n": "BLE",
    "BildID": "1001",
    "L\u00e4nets_namn": "Blekinge",
    "Ortens_namn": "Karlskrona",
    "Formul\u00e4r": "A",
    "F\u00f6rnamn": "Anna",
    "Efternamn": "Svensson",
    "Titel": "Fru",
    "Yrke": "Sjukv\u00e5rdare",
    "Adress": "Storgatan 5",
    "Bidrag_Kr": "5",
    "Bidrag_\u00f6re": "50",
    "F\u00f6delseuppgift": "1875",
    "Antal_namn": "10",
    "Summa_Kr": "50",
    "Summa_\u00f6re": "25",
    "\u00d6vriga_anteckningar": "",
}

ROSTRATT_ROW_NOTES: dict[str, str] = {
    "Volymens_l\u00e4n": "BLE",
    "BildID": "1004",
    "L\u00e4nets_namn": "Blekinge",
    "Ortens_namn": "Karlskrona",
    "Formul\u00e4r": "A",
    "F\u00f6rnamn": "Hilda",
    "Efternamn": "Pettersson",
    "Titel": "Fru",
    "Yrke": "Butiksbir\u00e4de",
    "Adress": "Drottninggatan 7",
    "Bidrag_Kr": "2",
    "Bidrag_\u00f6re": "25",
    "F\u00f6delseuppgift": "1878",
    "Antal_namn": "25",
    "Summa_Kr": "250",
    "Summa_\u00f6re": "75",
    "\u00d6vriga_anteckningar": "Gift med hamnarbetare",
}

# ---------------------------------------------------------------------------
# Test data: FKPR row (Astrid Lindberg)
# ---------------------------------------------------------------------------

FKPR_ROW: dict[str, str] = {
    "BILDID": "2001",
    "RAD": "1",
    "EFTERNAMN": "Lindberg",
    "FOERNAMN": "Astrid",
    "TITEL_YRKE": "L\u00e4rarinna",
    "ADRESS": "Vasagatan 10",
    "ADRESS_STRUKEN": "",
    "1911": "1",
    "1912": "1",
    "1913": "1",
    "1914": "1",
    "1915": "1",
    "1916": "1",
    "1917": "1",
    "1918": "1",
    "1919": "1",
    "1920": "1",
    "ANTECKNINGAR": "Styrelseledamot",
}

FKPR_ROW_PARTIAL: dict[str, str] = {
    "BILDID": "2005",
    "RAD": "5",
    "EFTERNAMN": "Holmgren",
    "FOERNAMN": "Signe",
    "TITEL_YRKE": "",
    "ADRESS": "Linn\u00e9gatan 15",
    "ADRESS_STRUKEN": "",
    "1911": "",
    "1912": "",
    "1913": "",
    "1914": "",
    "1915": "",
    "1916": "1",
    "1917": "1",
    "1918": "1",
    "1919": "1",
    "1920": "1",
    "ANTECKNINGAR": "Invald 1916",
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
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# RostrattRecord: basic fields
# ---------------------------------------------------------------------------


def test_rostratt_basic_fields() -> None:
    record = RostrattRecord.from_csv_row(ROSTRATT_ROW)
    assert record.lan == "Blekinge"
    assert record.ortens_namn == "Karlskrona"
    assert record.fornamn == "Anna"
    assert record.efternamn == "Svensson"
    assert record.titel == "Fru"
    assert record.yrke == "Sjukv\u00e5rdare"
    assert record.adress == "Storgatan 5"
    assert record.bidrag_kr == "5"
    assert record.bidrag_ore == "50"
    assert record.fodelseuppgift == "1875"


def test_rostratt_notes() -> None:
    record = RostrattRecord.from_csv_row(ROSTRATT_ROW_NOTES)
    assert record.ovriga_anteckningar == "Gift med hamnarbetare"


def test_rostratt_empty_notes() -> None:
    record = RostrattRecord.from_csv_row(ROSTRATT_ROW)
    assert record.ovriga_anteckningar == ""


# ---------------------------------------------------------------------------
# Rösträtt searchable text
# ---------------------------------------------------------------------------


def test_rostratt_searchable_text_contains_key_fields() -> None:
    record = RostrattRecord.from_csv_row(ROSTRATT_ROW)
    text = record.searchable_text
    assert "Anna" in text
    assert "Svensson" in text
    assert "Fru" in text
    assert "Sjukv\u00e5rdare" in text
    assert "Storgatan 5" in text
    assert "Karlskrona" in text
    assert "Blekinge" in text


def test_rostratt_searchable_text_skips_empty_fields() -> None:
    record = RostrattRecord.from_csv_row(ROSTRATT_ROW)
    text = record.searchable_text
    assert "  " not in text


# ---------------------------------------------------------------------------
# FKPRRecord: basic fields
# ---------------------------------------------------------------------------


def test_fkpr_basic_fields() -> None:
    record = FKPRRecord.from_csv_row(FKPR_ROW)
    assert record.efternamn == "Lindberg"
    assert record.foernamn == "Astrid"
    assert record.titel_yrke == "L\u00e4rarinna"
    assert record.adress == "Vasagatan 10"
    assert record.anteckningar == "Styrelseledamot"


def test_fkpr_all_years() -> None:
    record = FKPRRecord.from_csv_row(FKPR_ROW)
    assert record.membership_years == list(range(1911, 1921))


def test_fkpr_partial_years() -> None:
    record = FKPRRecord.from_csv_row(FKPR_ROW_PARTIAL)
    assert record.membership_years == [1916, 1917, 1918, 1919, 1920]


def test_fkpr_empty_title() -> None:
    record = FKPRRecord.from_csv_row(FKPR_ROW_PARTIAL)
    assert record.titel_yrke == ""


# ---------------------------------------------------------------------------
# FKPR searchable text
# ---------------------------------------------------------------------------


def test_fkpr_searchable_text_contains_key_fields() -> None:
    record = FKPRRecord.from_csv_row(FKPR_ROW)
    text = record.searchable_text
    assert "Lindberg" in text
    assert "Astrid" in text
    assert "L\u00e4rarinna" in text
    assert "Vasagatan 10" in text
    assert "Styrelseledamot" in text


def test_fkpr_searchable_text_skips_empty_fields() -> None:
    record = FKPRRecord.from_csv_row(FKPR_ROW_PARTIAL)
    text = record.searchable_text
    assert "  " not in text

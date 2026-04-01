"""Tests for Aktiebolag Pydantic models."""

from __future__ import annotations

import pytest

from ra_mcp_aktiebolag_lib.models import AktiebolagRecord, StyrelseRecord, _clean


# ---------------------------------------------------------------------------
# Test data: Company row with all fields
# ---------------------------------------------------------------------------

BOLAG_ROW: dict[str, str] = {
    "PostID": "1",
    "Bolagets_namn": "AB Separator",
    "Aldre_namn": "De Lavals Separator",
    "Argang": "1901",
    "Postadress": "Stockholm",
    "Bolagets_andamal": "Tillverkning och försäljning av separatorer",
    "Styrelsesate": "Stockholm",
    "Verkstall_dir": "John Bernström",
    "Aktiekapital_stam_A": "5000000",
}

STYRELSE_MAP: dict[int, str] = {
    1: "John Bernström, Gustaf De Laval",
    2: "Knut Agathon Wallenberg, Marcus Wallenberg",
}

# ---------------------------------------------------------------------------
# Test data: Board member row
# ---------------------------------------------------------------------------

STYRELSE_ROW: dict[str, str] = {
    "Id": "1",
    "PostID": "1",
    "Styrelsemed": "Bernström",
    "Fornamn": "John",
    "titel": "Direktör",
    "Kon": "M",
}

BOLAG_NAME_MAP: dict[int, str] = {
    1: "AB Separator",
    2: "Stockholms Enskilda Bank",
}


# ---------------------------------------------------------------------------
# _clean helper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("hello", "hello", id="normal-string"),
        pytest.param("-", "", id="dash-sentinel"),
        pytest.param(None, "", id="none-value"),
        pytest.param("", "", id="empty-string"),
        pytest.param("  spaces  ", "spaces", id="strips-whitespace"),
        pytest.param(" - ", "", id="dash-with-spaces"),
    ],
)
def test_clean(value: str | None, expected: str) -> None:
    assert _clean(value) == expected


# ---------------------------------------------------------------------------
# AktiebolagRecord: basic fields
# ---------------------------------------------------------------------------


def test_bolag_basic_fields() -> None:
    record = AktiebolagRecord.from_csv_row(BOLAG_ROW, STYRELSE_MAP)
    assert record.post_id == 1
    assert record.bolagets_namn == "AB Separator"
    assert record.aldre_namn == "De Lavals Separator"
    assert record.argang == "1901"
    assert record.postadress == "Stockholm"
    assert record.bolagets_andamal == "Tillverkning och försäljning av separatorer"
    assert record.styrelsesate == "Stockholm"
    assert record.verkstall_dir == "John Bernström"
    assert record.aktiekapital == "5000000"


def test_bolag_styrelse_join() -> None:
    record = AktiebolagRecord.from_csv_row(BOLAG_ROW, STYRELSE_MAP)
    assert record.styrelsemedlemmar == "John Bernström, Gustaf De Laval"


def test_bolag_without_styrelse_map() -> None:
    record = AktiebolagRecord.from_csv_row(BOLAG_ROW)
    assert record.styrelsemedlemmar == ""


def test_bolag_missing_post_id_in_map() -> None:
    record = AktiebolagRecord.from_csv_row(BOLAG_ROW, {999: "Nobody"})
    assert record.styrelsemedlemmar == ""


def test_bolag_dash_converts_to_empty() -> None:
    row = {**BOLAG_ROW, "Aldre_namn": "-", "Verkstall_dir": "-"}
    record = AktiebolagRecord.from_csv_row(row)
    assert record.aldre_namn == ""
    assert record.verkstall_dir == ""


# ---------------------------------------------------------------------------
# AktiebolagRecord: searchable text
# ---------------------------------------------------------------------------


def test_bolag_searchable_text() -> None:
    record = AktiebolagRecord.from_csv_row(BOLAG_ROW, STYRELSE_MAP)
    text = record.searchable_text
    assert "AB Separator" in text
    assert "De Lavals Separator" in text
    assert "separatorer" in text
    assert "Stockholm" in text
    assert "John Bernström" in text


def test_bolag_searchable_text_skips_empty() -> None:
    row = {**BOLAG_ROW, "Aldre_namn": "-", "Verkstall_dir": "-"}
    record = AktiebolagRecord.from_csv_row(row)
    text = record.searchable_text
    assert "  " not in text


# ---------------------------------------------------------------------------
# StyrelseRecord: basic fields
# ---------------------------------------------------------------------------


def test_styrelse_basic_fields() -> None:
    record = StyrelseRecord.from_csv_row(STYRELSE_ROW, BOLAG_NAME_MAP)
    assert record.id == 1
    assert record.post_id == 1
    assert record.styrelsemed == "Bernström"
    assert record.fornamn == "John"
    assert record.titel == "Direktör"
    assert record.kon == "M"


def test_styrelse_bolag_join() -> None:
    record = StyrelseRecord.from_csv_row(STYRELSE_ROW, BOLAG_NAME_MAP)
    assert record.bolagets_namn == "AB Separator"


def test_styrelse_without_bolag_map() -> None:
    record = StyrelseRecord.from_csv_row(STYRELSE_ROW)
    assert record.bolagets_namn == ""


def test_styrelse_missing_post_id_in_map() -> None:
    record = StyrelseRecord.from_csv_row(STYRELSE_ROW, {999: "No Company"})
    assert record.bolagets_namn == ""


# ---------------------------------------------------------------------------
# StyrelseRecord: searchable text
# ---------------------------------------------------------------------------


def test_styrelse_searchable_text() -> None:
    record = StyrelseRecord.from_csv_row(STYRELSE_ROW, BOLAG_NAME_MAP)
    text = record.searchable_text
    assert "Bernström" in text
    assert "John" in text
    assert "Direktör" in text
    assert "AB Separator" in text


def test_styrelse_searchable_text_skips_empty() -> None:
    row = {**STYRELSE_ROW, "titel": "-"}
    record = StyrelseRecord.from_csv_row(row)
    text = record.searchable_text
    assert "  " not in text

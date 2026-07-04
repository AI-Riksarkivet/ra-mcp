"""Tests for FilmregRecord Pydantic model."""

import pytest

from ra_mcp_filmcensur_lib.models import FilmregRecord, _clean


# ---------------------------------------------------------------------------
# Test data: Spelfilm with all fields populated
# ---------------------------------------------------------------------------

SPELFILM_ROW: dict[str, str] = {
    "Granskningsnummer": "1001",
    "Titel_Org": "The Great Train Robbery",
    "Titel_Svensk": "Det stora tågrånet",
    "Titel_Annan": "-",
    "Produktionsaar": "1903",
    "Filmkategori": "Spelfilm",
    "Filmtyp": "Stumfilm",
    "Produktionsland": "USA",
    "Fri_Text": "En brottslingsliga rånar ett tåg i västra USA",
    "Beslutsdatum": "1911-03-15",
    "AAldersgraens": "Barntillåten",
    "Klipp_Antal": "0",
    "Producent": "Edison Manufacturing",
    "Beslut_laengd_foere_tid": "12 min",
    "Noteringar": "Tidigt actiondrama",
}

# ---------------------------------------------------------------------------
# Test data: record with many dash/empty fields
# ---------------------------------------------------------------------------

MINIMAL_ROW: dict[str, str] = {
    "Granskningsnummer": "1003",
    "Titel_Org": "-",
    "Titel_Svensk": "Stockholmsbilder",
    "Titel_Annan": "-",
    "Produktionsaar": "1912",
    "Filmkategori": "Dokumentär",
    "Filmtyp": "Stumfilm",
    "Produktionsland": "Sverige",
    "Fri_Text": "Vyer från Stockholm med folklivsscener",
    "Beslutsdatum": "1912-06-10",
    "AAldersgraens": "Barntillåten",
    "Klipp_Antal": "0",
    "Producent": "-",
    "Beslut_laengd_foere_tid": "8 min",
    "Noteringar": "-",
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
# Basic fields
# ---------------------------------------------------------------------------


def test_spelfilm_basic_fields() -> None:
    record = FilmregRecord.from_csv_row(SPELFILM_ROW)
    assert record.granskningsnummer == 1001
    assert record.titel_org == "The Great Train Robbery"
    assert record.titel_svensk == "Det stora tågrånet"
    assert record.produktionsaar == "1903"
    assert record.filmkategori == "Spelfilm"
    assert record.filmtyp == "Stumfilm"
    assert record.produktionsland == "USA"
    assert record.producent == "Edison Manufacturing"
    assert record.aaldersgraens == "Barntillåten"
    assert record.klipp_antal == "0"
    assert record.beslut_laengd == "12 min"
    assert record.beslutsdatum == "1911-03-15"
    assert record.noteringar == "Tidigt actiondrama"


# ---------------------------------------------------------------------------
# Dash sentinel → empty conversion
# ---------------------------------------------------------------------------


def test_dash_converts_to_empty() -> None:
    record = FilmregRecord.from_csv_row(MINIMAL_ROW)
    assert record.titel_org == ""
    assert record.titel_annan == ""
    assert record.producent == ""
    assert record.noteringar == ""


# ---------------------------------------------------------------------------
# searchable_text
# ---------------------------------------------------------------------------


def test_searchable_text_contains_key_fields() -> None:
    record = FilmregRecord.from_csv_row(SPELFILM_ROW)
    text = record.searchable_text
    assert "The Great Train Robbery" in text
    assert "Det stora tågrånet" in text
    assert "USA" in text
    assert "Spelfilm" in text
    assert "Edison Manufacturing" in text
    assert "Tidigt actiondrama" in text
    assert "Barntillåten" in text


def test_searchable_text_skips_empty_fields() -> None:
    record = FilmregRecord.from_csv_row(MINIMAL_ROW)
    text = record.searchable_text
    # titel_org is "-" → empty, should not appear
    assert "-" not in text.split()
    assert "  " not in text


def test_searchable_text_no_double_spaces() -> None:
    record = FilmregRecord.from_csv_row(SPELFILM_ROW)
    text = record.searchable_text
    assert "  " not in text

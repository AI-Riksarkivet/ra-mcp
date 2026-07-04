"""Tests for RosenbergRecord Pydantic model."""

import pytest

from ra_mcp_rosenberg_lib.models import RosenbergRecord, _clean


# ---------------------------------------------------------------------------
# Test data: Stockholm with industries
# ---------------------------------------------------------------------------

STOCKHOLM_ROW: dict[str, str] = {
    "PostID": "1",
    "URL": "http://example.com/1",
    "Plats": "Stockholm",
    "Forsamling": "Klara",
    "Harad": "Stockholms stad",
    "Tingslag": "",
    "Lan": "Stockholms län",
    "Beskrivning": "Rikets hufvudstad vid Mälarens utlopp i Salt-sjön",
    "kalkbränning": "",
    "tändstikor": "",
    "fyr": "",
    "färjställe": "",
    "fisk": "",
    "bränneri": "",
    "stambana": "",
    "jernverk": "",
    "tegelbruk": "",
    "mjölsfabrik": "",
    "gjuteri": "",
    "gästgifveri": "1",
    "säteri": "",
    "jernväg": "",
    "grufva": "",
    "såg": "1",
    "qvarn": "",
}

# ---------------------------------------------------------------------------
# Test data: minimal record
# ---------------------------------------------------------------------------

MINIMAL_ROW: dict[str, str] = {
    "PostID": "99",
    "URL": "",
    "Plats": "Testplats",
    "Forsamling": "",
    "Harad": "",
    "Tingslag": "",
    "Lan": "",
    "Beskrivning": "",
    "kalkbränning": "",
    "tändstikor": "",
    "fyr": "",
    "färjställe": "",
    "fisk": "",
    "bränneri": "",
    "stambana": "",
    "jernverk": "",
    "tegelbruk": "",
    "mjölsfabrik": "",
    "gjuteri": "",
    "gästgifveri": "",
    "säteri": "",
    "jernväg": "",
    "grufva": "",
    "såg": "",
    "qvarn": "",
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
# Basic fields
# ---------------------------------------------------------------------------


def test_stockholm_basic_fields() -> None:
    record = RosenbergRecord.from_csv_row(STOCKHOLM_ROW)
    assert record.post_id == 1
    assert record.url == "http://example.com/1"
    assert record.plats == "Stockholm"
    assert record.forsamling == "Klara"
    assert record.harad == "Stockholms stad"
    assert record.tingslag == ""
    assert record.lan == "Stockholms län"
    assert record.beskrivning == "Rikets hufvudstad vid Mälarens utlopp i Salt-sjön"


# ---------------------------------------------------------------------------
# Industry flags
# ---------------------------------------------------------------------------


def test_stockholm_industry_flags() -> None:
    record = RosenbergRecord.from_csv_row(STOCKHOLM_ROW)
    assert record.gastgifveri == "1"
    assert record.sag == "1"
    assert record.jernverk == ""
    assert record.grufva == ""


def test_industries_property() -> None:
    record = RosenbergRecord.from_csv_row(STOCKHOLM_ROW)
    industries = record.industries
    assert "Gästgifveri" in industries
    assert "Såg" in industries
    assert len(industries) == 2


def test_industries_empty_for_minimal() -> None:
    record = RosenbergRecord.from_csv_row(MINIMAL_ROW)
    assert record.industries == []


# ---------------------------------------------------------------------------
# searchable_text
# ---------------------------------------------------------------------------


def test_searchable_text_contains_key_fields() -> None:
    record = RosenbergRecord.from_csv_row(STOCKHOLM_ROW)
    text = record.searchable_text
    assert "Stockholm" in text
    assert "Klara" in text
    assert "Stockholms stad" in text
    assert "Stockholms län" in text
    assert "hufvudstad" in text


def test_searchable_text_skips_empty_fields() -> None:
    record = RosenbergRecord.from_csv_row(MINIMAL_ROW)
    text = record.searchable_text
    assert text == "Testplats"


def test_searchable_text_no_double_spaces() -> None:
    record = RosenbergRecord.from_csv_row(STOCKHOLM_ROW)
    text = record.searchable_text
    assert "  " not in text

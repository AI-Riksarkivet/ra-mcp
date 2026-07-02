"""Tests for SBLRecord Pydantic model."""

import pytest

from ra_mcp_sbl_lib.models import SBLRecord, _clean, _parse_int


# ---------------------------------------------------------------------------
# Test data: person article (Gustaf R Abelin)
# ---------------------------------------------------------------------------

PERSON_ROW: dict[str, str] = {
    "Article id": "5491",
    "Svenskt biografiskt lexikon (SBL): URI": "https://sok.riksarkivet.se/sbl/Presentation.aspx?id=5491",
    "Type of article": "Person article",
    "SBL volume number": "1",
    "Page number in volume": "5",
    "Surname": "Abelin",
    "Given name": "Gustaf R",
    "Gender": "m",
    "Occupation, royal title, rank": "Arméofficer, Lantförsvarsminister",
    "Prefix to year of birth": "",
    "Year of birth": "1819",
    "Month of birth": "5",
    "Day of birth": "17",
    "Place of birth": "Linköpings Domkyrkoförsamling",
    "Comment on place of birth": "",
    "Place of birth (physical location)": "NULL",
    "Prefix to year of death": "",
    "Year of death": "1903",
    "Month of death": "9",
    "Day of death": "19",
    "Place of death": "Kvillinge församling",
    "Comment on place of death": "på Björnsnäs",
    "Place of death (physical location)": "NULL",
    "Id of main article": "NULL",
    "Curriculum vitae": "Gustaf Rudolf Abelin, f. 17 maj 1819 i Linköping",
    "Archive": "",
    "Printed works": "Några upplysningar angående milis-systemet",
    "Sources": "Militaria: ansökn. och meritförteckn., RA",
    "Article author": "S. Drakenberg.",
    "Image file 1": "https://sok.riksarkivet.se/sbl/bilder/5491_7_001_00000006_0.jpg",
    "Image 1 description": "O. R. Abelin. Fotografi.",
    "Image file 2": "NULL",
    "Image 2 description": "NULL",
    "Image file 3": "NULL",
    "Image 3 description": "NULL",
    "Image file 4": "NULL",
    "Image 4 description": "NULL",
    "Image file 5": "NULL",
    "Image 5 description": "NULL",
    "Image file 6": "NULL",
    "Image 6 description": "NULL",
    "Image file 7": "NULL",
    "Image 7 description": "NULL",
    "Image file 8": "NULL",
    "Image 8 description": "NULL",
    "Image file 9": "NULL",
    "Image 9 description": "NULL",
}

# ---------------------------------------------------------------------------
# Test data: family article (no dates, gender="-")
# ---------------------------------------------------------------------------

FAMILY_ROW: dict[str, str] = {
    "Article id": "5490",
    "Svenskt biografiskt lexikon (SBL): URI": "https://sok.riksarkivet.se/sbl/Presentation.aspx?id=5490",
    "Type of article": "Family article",
    "SBL volume number": "1",
    "Page number in volume": "4",
    "Surname": "Abelin",
    "Given name": "NULL",
    "Gender": "-",
    "Occupation, royal title, rank": "NULL",
    "Prefix to year of birth": "NULL",
    "Year of birth": "NULL",
    "Month of birth": "NULL",
    "Day of birth": "NULL",
    "Place of birth": "NULL",
    "Comment on place of birth": "NULL",
    "Place of birth (physical location)": "NULL",
    "Prefix to year of death": "NULL",
    "Year of death": "NULL",
    "Month of death": "NULL",
    "Day of death": "NULL",
    "Place of death": "NULL",
    "Comment on place of death": "NULL",
    "Place of death (physical location)": "NULL",
    "Id of main article": "NULL",
    "Curriculum vitae": "NULL",
    "Archive": "NULL",
    "Printed works": "NULL",
    "Sources": "NULL",
    "Article author": "NULL",
    "Image file 1": "NULL",
    "Image 1 description": "NULL",
    "Image file 2": "NULL",
    "Image 2 description": "NULL",
    "Image file 3": "NULL",
    "Image 3 description": "NULL",
    "Image file 4": "NULL",
    "Image 4 description": "NULL",
    "Image file 5": "NULL",
    "Image 5 description": "NULL",
    "Image file 6": "NULL",
    "Image 6 description": "NULL",
    "Image file 7": "NULL",
    "Image 7 description": "NULL",
    "Image file 8": "NULL",
    "Image 8 description": "NULL",
    "Image file 9": "NULL",
    "Image 9 description": "NULL",
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
# _parse_int helper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("1819", 1819, id="valid-int"),
        pytest.param("0", 0, id="zero"),
        pytest.param("NULL", None, id="null-sentinel"),
        pytest.param(None, None, id="none-value"),
        pytest.param("", None, id="empty-string"),
        pytest.param("abc", None, id="non-numeric"),
        pytest.param(" 42 ", 42, id="padded-int"),
    ],
)
def test_parse_int(value: str | None, expected: int | None) -> None:
    assert _parse_int(value) == expected


# ---------------------------------------------------------------------------
# Person article: basic fields
# ---------------------------------------------------------------------------


def test_person_basic_fields() -> None:
    record = SBLRecord.from_csv_row(PERSON_ROW)
    assert record.article_id == 5491
    assert record.surname == "Abelin"
    assert record.given_name == "Gustaf R"
    assert record.gender == "m"
    assert record.occupation == "Arméofficer, Lantförsvarsminister"
    assert record.article_type == "Person article"
    assert record.volume_number == "1"
    assert record.page_number == "5"


# ---------------------------------------------------------------------------
# SBL URI
# ---------------------------------------------------------------------------


def test_sbl_uri() -> None:
    record = SBLRecord.from_csv_row(PERSON_ROW)
    assert record.sbl_uri == "https://sok.riksarkivet.se/sbl/Presentation.aspx?id=5491"


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------


def test_person_birth_dates() -> None:
    record = SBLRecord.from_csv_row(PERSON_ROW)
    assert record.birth_year == 1819
    assert record.birth_month == 5
    assert record.birth_day == 17
    assert record.birth_year_prefix == ""


def test_person_death_dates() -> None:
    record = SBLRecord.from_csv_row(PERSON_ROW)
    assert record.death_year == 1903
    assert record.death_month == 9
    assert record.death_day == 19
    assert record.death_year_prefix == ""


def test_family_has_no_dates() -> None:
    record = SBLRecord.from_csv_row(FAMILY_ROW)
    assert record.birth_year is None
    assert record.birth_month is None
    assert record.birth_day is None
    assert record.death_year is None
    assert record.death_month is None
    assert record.death_day is None


# ---------------------------------------------------------------------------
# Place fields
# ---------------------------------------------------------------------------


def test_person_birth_place() -> None:
    record = SBLRecord.from_csv_row(PERSON_ROW)
    assert record.birth_place == "Linköpings Domkyrkoförsamling"
    assert record.birth_place_comment == ""
    assert record.birth_place_physical == ""


def test_person_death_place() -> None:
    record = SBLRecord.from_csv_row(PERSON_ROW)
    assert record.death_place == "Kvillinge församling"
    assert record.death_place_comment == "på Björnsnäs"
    assert record.death_place_physical == ""


# ---------------------------------------------------------------------------
# NULL → empty conversion
# ---------------------------------------------------------------------------


def test_null_converts_to_empty() -> None:
    record = SBLRecord.from_csv_row(FAMILY_ROW)
    assert record.given_name == ""
    assert record.occupation == ""
    assert record.cv == ""
    assert record.archive == ""
    assert record.printed_works == ""
    assert record.sources == ""
    assert record.article_author == ""
    assert record.birth_place == ""
    assert record.death_place == ""
    assert record.main_article_id == ""


def test_person_null_physical_locations() -> None:
    """Physical location columns with NULL should become empty strings."""
    record = SBLRecord.from_csv_row(PERSON_ROW)
    assert record.birth_place_physical == ""
    assert record.death_place_physical == ""


# ---------------------------------------------------------------------------
# Family article specifics
# ---------------------------------------------------------------------------


def test_family_article_fields() -> None:
    record = SBLRecord.from_csv_row(FAMILY_ROW)
    assert record.article_id == 5490
    assert record.surname == "Abelin"
    assert record.gender == "-"
    assert record.article_type == "Family article"


# ---------------------------------------------------------------------------
# Image collection
# ---------------------------------------------------------------------------


def test_person_has_one_image() -> None:
    record = SBLRecord.from_csv_row(PERSON_ROW)
    assert len(record.image_files) == 1
    assert record.image_files[0] == "https://sok.riksarkivet.se/sbl/bilder/5491_7_001_00000006_0.jpg"
    assert len(record.image_descriptions) == 1
    assert record.image_descriptions[0] == "O. R. Abelin. Fotografi."


def test_family_has_no_images() -> None:
    record = SBLRecord.from_csv_row(FAMILY_ROW)
    assert record.image_files == []
    assert record.image_descriptions == []


def test_multiple_images_collected() -> None:
    """When multiple image columns are non-NULL, all are collected in order."""
    row = {**PERSON_ROW}
    row["Image file 2"] = "https://example.com/img2.jpg"
    row["Image 2 description"] = "Second image"
    row["Image file 5"] = "https://example.com/img5.jpg"
    row["Image 5 description"] = "Fifth image"
    record = SBLRecord.from_csv_row(row)
    assert len(record.image_files) == 3
    assert record.image_files[1] == "https://example.com/img2.jpg"
    assert record.image_descriptions[1] == "Second image"
    assert record.image_files[2] == "https://example.com/img5.jpg"
    assert record.image_descriptions[2] == "Fifth image"


# ---------------------------------------------------------------------------
# searchable_text
# ---------------------------------------------------------------------------


def test_searchable_text_contains_key_fields() -> None:
    record = SBLRecord.from_csv_row(PERSON_ROW)
    text = record.searchable_text
    assert "Abelin" in text
    assert "Gustaf R" in text
    assert "Arméofficer" in text
    assert "Gustaf Rudolf Abelin" in text
    assert "Linköpings Domkyrkoförsamling" in text
    assert "Kvillinge församling" in text
    assert "Några upplysningar angående milis-systemet" in text
    assert "Militaria" in text


def test_searchable_text_skips_empty_fields() -> None:
    record = SBLRecord.from_csv_row(FAMILY_ROW)
    text = record.searchable_text
    assert text == "Abelin"
    assert "  " not in text


def test_searchable_text_no_double_spaces() -> None:
    """Empty fields should not cause double spaces in searchable text."""
    record = SBLRecord.from_csv_row(PERSON_ROW)
    text = record.searchable_text
    assert "  " not in text

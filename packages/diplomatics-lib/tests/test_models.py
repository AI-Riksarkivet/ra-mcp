"""Tests for SDHKRecord and MPORecord Pydantic models."""

import pytest

from ra_mcp_diplomatics_lib.models import MPORecord, SDHKRecord


# ---------------------------------------------------------------------------
# SDHKRecord fixtures
# ---------------------------------------------------------------------------

SDHK_CSV_ROW: dict[str, str] = {
    "Id": "12345",
    "Title": "Brev om arv",
    "Author": "Birger jarl",
    "Date": "1250",
    "Place": "Stockholm",
    "Lang": "Latin",
    "Summary": "Donation av gods till klostret",
    "Comments": "Vattenmärke synligt",
    "Edition": "DS 1234",
    "Seals": "Sigill av vax",
    "Original": "RA",
    "MedievalCopy": "",
    "PostmedievalCopy": "KB avskrift",
    "MedievalReg": "",
    "PostmedievalReg": "",
    "Photocopy": "",
    "Print": "SRS II:1",
    "PrintReg": "",
    "Facsimile": "",
    "Translation": "Swedish translation exists",
    "Additional": "Extra note here",
}


def test_sdhk_from_csv_row_basic_fields() -> None:
    record = SDHKRecord.from_csv_row(SDHK_CSV_ROW)
    assert record.id == 12345
    assert record.title == "Brev om arv"
    assert record.author == "Birger jarl"
    assert record.date == "1250"
    assert record.place == "Stockholm"
    assert record.language == "Latin"
    assert record.summary == "Donation av gods till klostret"


def test_sdhk_from_csv_row_all_string_fields() -> None:
    record = SDHKRecord.from_csv_row(SDHK_CSV_ROW)
    assert record.comments == "Vattenmärke synligt"
    assert record.edition == "DS 1234"
    assert record.seals == "Sigill av vax"
    assert record.original == "RA"
    assert record.medieval_copy == ""
    assert record.postmedieval_copy == "KB avskrift"
    assert record.printed == "SRS II:1"
    assert record.translation == "Swedish translation exists"
    assert record.additional == "Extra note here"


def test_sdhk_string_fields_default_to_empty() -> None:
    """Missing optional CSV columns should produce empty strings."""
    minimal_row = {"Id": "1"}
    record = SDHKRecord.from_csv_row(minimal_row)
    assert record.id == 1
    assert record.title == ""
    assert record.author == ""
    assert record.summary == ""
    assert record.additional == ""


def test_sdhk_searchable_text_contains_expected_fields() -> None:
    record = SDHKRecord.from_csv_row(SDHK_CSV_ROW)
    text = record.searchable_text
    assert "Birger jarl" in text
    assert "Donation av gods till klostret" in text
    assert "DS 1234" in text
    assert "Vattenmärke synligt" in text
    assert "Sigill av vax" in text
    assert "Extra note here" in text


def test_sdhk_searchable_text_excludes_non_searchable_fields() -> None:
    record = SDHKRecord.from_csv_row(SDHK_CSV_ROW)
    text = record.searchable_text
    # title, date, place, language are not part of searchable_text
    assert "Stockholm" not in text
    assert "1250" not in text


def test_sdhk_searchable_text_skips_empty_parts() -> None:
    """Empty string fields should not appear as stray spaces."""
    minimal_row = {"Id": "99", "Author": "Some Author"}
    record = SDHKRecord.from_csv_row(minimal_row)
    text = record.searchable_text
    assert text == "Some Author"
    assert "  " not in text


def test_sdhk_manifest_url_format() -> None:
    record = SDHKRecord.from_csv_row(SDHK_CSV_ROW)
    assert record.manifest_url == "https://lbiiif.riksarkivet.se/sdhk!12345/manifest"


def test_sdhk_manifest_url_uses_record_id() -> None:
    record = SDHKRecord.from_csv_row({"Id": "42"})
    assert record.manifest_url == "https://lbiiif.riksarkivet.se/sdhk!42/manifest"


def test_sdhk_bildvisning_url_format() -> None:
    record = SDHKRecord.from_csv_row(SDHK_CSV_ROW)
    assert record.bildvisning_url == "https://sok.riksarkivet.se/bildvisning/sdhk!12345"


# ---------------------------------------------------------------------------
# MPORecord fixtures
# ---------------------------------------------------------------------------

MPO_CSV_ROW: dict[str, str] = {
    "signatur": "7890",
    "bildbetrachter": "https://example.com/viewer/7890",
    "institution": "Riksarkivet",
    "inst2": "Medeltidssamlingen",
    "ranr": "RA-7890",
    "ccmsignum": "CCM-001",
    "bestandsbezeichnung": "Pergamentsamlingen",
    "bestandssignatur": "Perg 1234",
    "buchschmuck": "Rödstreckade initialer",
    "beschreibstoff": "Pergament",
    "blattzahl": "42",
    "spaltenzahl": "2",
    "zeilenzahl1": "30",
    "zeilenzahl2": "32",
    "format": "235 x 165",
    "schriftraum1": "185 x 120",
    "schriftraum2": "",
    "schäden": "Fuktskada i nedre marginal",
    "lagenanmerkungen": "8+8+8+8+10",
    "schrift": "Textura",
    "rubrizierung": "Rött och blått",
    "notation": "Kvadratnotation",
    "notenlinien": "4",
    "anmerkungen": "Ex libris klistrat på pärm",
    "sachtitel": "Antiphonar",
    "sachgruppe": "Liturgi",
    "titel": "Antifonarium Scarense",
    "autor1": "Okänd",
    "autor2": "",
    "entstehungsort": "Skara",
    "anwendungsort": "Skara domkyrka",
    "datierung": "ca 1300",
    "wiegendruck": "",
    "codex": "Ja",
    "literatur": "Klemming 1885",
    "inhalt": "Mässans proprium och ordinarium",
    "iiif_manifest": "https://example.com/iiif/7890/manifest",
}


def test_mpo_from_csv_row_basic_fields() -> None:
    record = MPORecord.from_csv_row(MPO_CSV_ROW)
    assert record.id == 7890
    assert record.institution == "Riksarkivet"
    assert record.institution_detail == "Medeltidssamlingen"
    assert record.material == "Pergament"
    assert record.dating == "ca 1300"


def test_mpo_from_csv_row_all_mapped_fields() -> None:
    record = MPORecord.from_csv_row(MPO_CSV_ROW)
    assert record.bildvisning_url == "https://example.com/viewer/7890"
    assert record.ra_number == "RA-7890"
    assert record.ccm_signum == "CCM-001"
    assert record.collection == "Pergamentsamlingen"
    assert record.volume_signature == "Perg 1234"
    assert record.decoration == "Rödstreckade initialer"
    assert record.leaf_count == "42"
    assert record.column_count == "2"
    assert record.line_count == "30"
    assert record.line_count2 == "32"
    assert record.format_size == "235 x 165"
    assert record.writing_space == "185 x 120"
    assert record.damage == "Fuktskada i nedre marginal"
    assert record.quire_notes == "8+8+8+8+10"
    assert record.script == "Textura"
    assert record.rubrication == "Rött och blått"
    assert record.notation == "Kvadratnotation"
    assert record.staff_lines == "4"
    assert record.notes == "Ex libris klistrat på pärm"
    assert record.manuscript_type == "Antiphonar"
    assert record.category == "Liturgi"
    assert record.title == "Antifonarium Scarense"
    assert record.author == "Okänd"
    assert record.origin_place == "Skara"
    assert record.use_place == "Skara domkyrka"
    assert record.incunabulum == ""
    assert record.codex == "Ja"
    assert record.literature == "Klemming 1885"
    assert record.content == "Mässans proprium och ordinarium"
    assert record.iiif_manifest == "https://example.com/iiif/7890/manifest"


def test_mpo_string_fields_default_to_empty() -> None:
    """Missing optional CSV columns should produce empty strings."""
    minimal_row = {"signatur": "1"}
    record = MPORecord.from_csv_row(minimal_row)
    assert record.id == 1
    assert record.institution == ""
    assert record.title == ""
    assert record.iiif_manifest == ""


def test_mpo_manifest_url_returns_iiif_manifest() -> None:
    record = MPORecord.from_csv_row(MPO_CSV_ROW)
    assert record.manifest_url == "https://example.com/iiif/7890/manifest"


def test_mpo_manifest_url_with_no_manifest_returns_empty() -> None:
    record = MPORecord.from_csv_row({"signatur": "1"})
    assert record.manifest_url == ""


def test_mpo_searchable_text_contains_expected_fields() -> None:
    record = MPORecord.from_csv_row(MPO_CSV_ROW)
    text = record.searchable_text
    assert "Antiphonar" in text
    assert "Antifonarium Scarense" in text
    assert "Okänd" in text
    assert "Mässans proprium och ordinarium" in text
    assert "Ex libris klistrat på pärm" in text
    assert "Rödstreckade initialer" in text
    assert "Klemming 1885" in text
    assert "Fuktskada i nedre marginal" in text


def test_mpo_searchable_text_skips_empty_parts() -> None:
    minimal_row = {"signatur": "5", "titel": "Codex Aureus"}
    record = MPORecord.from_csv_row(minimal_row)
    text = record.searchable_text
    assert text == "Codex Aureus"
    assert "  " not in text


@pytest.mark.parametrize(
    "sdhk_id,expected_manifest",
    [
        pytest.param("1", "https://lbiiif.riksarkivet.se/sdhk!1/manifest", id="id-1"),
        pytest.param("99999", "https://lbiiif.riksarkivet.se/sdhk!99999/manifest", id="id-99999"),
        pytest.param("100", "https://lbiiif.riksarkivet.se/sdhk!100/manifest", id="id-100"),
    ],
)
def test_sdhk_manifest_url_parametrized(sdhk_id: str, expected_manifest: str) -> None:
    record = SDHKRecord.from_csv_row({"Id": sdhk_id})
    assert record.manifest_url == expected_manifest

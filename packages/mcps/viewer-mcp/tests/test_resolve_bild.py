"""Tests for bild_id resolution (bild_resolve_document and _parse_bild_id)."""

import pytest

from ra_mcp_viewer_mcp.resolve import _parse_bild_id, bild_resolve_document


# ---------------------------------------------------------------------------
# _parse_bild_id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bild_id,expected",
    [
        pytest.param("C0056829_00001", ("C0056829", "00001"), id="standard"),
        pytest.param("H0000459_00005", ("H0000459", "00005"), id="h-prefix"),
        pytest.param("A0012345_00100", ("A0012345", "00100"), id="a-prefix"),
        pytest.param("R0001203_00010", ("R0001203", "00010"), id="r-prefix"),
    ],
)
def test_parse_bild_id(bild_id: str, expected: tuple[str, str]):
    assert _parse_bild_id(bild_id) == expected


@pytest.mark.parametrize(
    "bad_id",
    [
        pytest.param("", id="empty"),
        pytest.param("C0056829", id="no-underscore"),
        pytest.param("_00001", id="leading-underscore-only"),
    ],
)
def test_parse_bild_id_invalid(bad_id: str):
    with pytest.raises(ValueError, match="Invalid bild_id format"):
        _parse_bild_id(bad_id)


# ---------------------------------------------------------------------------
# bild_resolve_document
# ---------------------------------------------------------------------------


def test_resolve_single_bild_id():
    result = bild_resolve_document(["C0056829_00001"])

    assert len(result.image_urls) == 1
    assert "C0056829_00001" in result.image_urls[0]
    assert result.image_urls[0].startswith("https://lbiiif.riksarkivet.se/")

    assert len(result.text_layer_urls) == 1
    assert "C0056829_00001.xml" in result.text_layer_urls[0]

    assert len(result.bildvisning_urls) == 1
    assert "C0056829_00001" in result.bildvisning_urls[0]

    assert result.page_numbers == [1]
    assert "C0056829_00001" in result.document_info


def test_resolve_multiple_bild_ids():
    ids = ["C0056829_00001", "C0056829_00002", "C0056829_00003"]
    result = bild_resolve_document(ids)

    assert len(result.image_urls) == 3
    assert len(result.text_layer_urls) == 3
    assert len(result.bildvisning_urls) == 3
    assert result.page_numbers == [1, 2, 3]


def test_resolve_with_highlight():
    result = bild_resolve_document(["C0056829_00001"], highlight_term="Anna")

    assert "Anna" in result.bildvisning_urls[0]


def test_resolve_strips_whitespace():
    result = bild_resolve_document(["  C0056829_00001  "])

    assert len(result.image_urls) == 1
    assert "C0056829_00001" in result.image_urls[0]


def test_resolve_empty_list_raises():
    with pytest.raises(ValueError, match="must not be empty"):
        bild_resolve_document([])


def test_resolve_invalid_id_raises():
    with pytest.raises(ValueError, match="Invalid bild_id format"):
        bild_resolve_document(["bad-id"])


def test_resolve_url_structure():
    """Verify the generated URLs follow Riksarkivet's conventions."""
    result = bild_resolve_document(["C0056829_00001"])

    # IIIF: https://lbiiif.riksarkivet.se/arkis!{manifest}_{page}/full/max/0/default.jpg
    assert result.image_urls[0] == "https://lbiiif.riksarkivet.se/arkis!C0056829_00001/full/max/0/default.jpg"

    # ALTO: https://sok.riksarkivet.se/dokument/alto/{first4}/{manifest}/{manifest}_{page}.xml
    assert result.text_layer_urls[0] == "https://sok.riksarkivet.se/dokument/alto/C005/C0056829/C0056829_00001.xml"

    # Bildvisning: https://sok.riksarkivet.se/bildvisning/{manifest}_{page}
    assert result.bildvisning_urls[0] == "https://sok.riksarkivet.se/bildvisning/C0056829_00001"


def test_resolve_compound_manifest_id():
    """bild_id with a longer manifest portion (e.g. H0000459_00005)."""
    result = bild_resolve_document(["H0000459_00005"])

    assert "H0000459_00005" in result.image_urls[0]
    assert result.page_numbers == [5]

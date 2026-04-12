"""Tests for DDS formatter — verifies bild_id and reference code appear in output."""

from ra_mcp_dds_lib.search_operations import SearchResult
from ra_mcp_dds_mcp.formatter import format_doda_results, format_fodelse_results, format_vigsel_results


def _fodelse_result(**overrides) -> SearchResult:
    rec = {
        "postid": "123",
        "fornamn": "Anna",
        "kon": "Kvinna",
        "datum": "1850-03-15",
        "forsamling": "Mora",
        "lan": "Kopparbergs",
        "far_fornamn": "Erik",
        "far_efternamn": "Andersson",
        "far_yrke": "Bonde",
        "mor_fornamn": "Karin",
        "mor_efternamn": "",
        "fodelseort": "",
        "anm": "",
        "referenskod": "SE/LLA/13008",
        "volym": "C I:5",
        "bild_id": "C0056829_00001",
    }
    rec.update(overrides)
    return SearchResult(records=[rec], total_hits=1, keyword="Anna", limit=25, offset=0)


def test_fodelse_includes_bild_id():
    text = format_fodelse_results(_fodelse_result())
    assert "Bild ID: C0056829_00001" in text


def test_fodelse_includes_ref():
    text = format_fodelse_results(_fodelse_result())
    assert "Ref: SE/LLA/13008" in text


def test_fodelse_includes_viewer_tip():
    text = format_fodelse_results(_fodelse_result())
    assert "view_bild" in text


def test_fodelse_omits_empty_bild_id():
    text = format_fodelse_results(_fodelse_result(bild_id=""))
    assert "Bild ID:" not in text


def _doda_result(**overrides) -> SearchResult:
    rec = {
        "postid": "456",
        "fornamn": "Per",
        "efternamn": "Larsson",
        "datum": "1890-12-01",
        "forsamling": "Lund",
        "lan": "Malmöhus",
        "yrke": "",
        "hemort": "",
        "alder": "72",
        "dodsorsak": "",
        "dodsorsak_klassificerat": "",
        "anhorig_fornamn": "",
        "anhorig_efternamn": "",
        "anhorig_yrke": "",
        "anhorig_relation": "",
        "anm": "",
        "referenskod": "SE/LLA/13200",
        "volym": "F I:3",
        "bild_id": "A0012345_00010",
    }
    rec.update(overrides)
    return SearchResult(records=[rec], total_hits=1, keyword="Per", limit=25, offset=0)


def test_doda_includes_bild_id():
    text = format_doda_results(_doda_result())
    assert "Bild ID: A0012345_00010" in text


def test_doda_includes_ref():
    text = format_doda_results(_doda_result())
    assert "Ref: SE/LLA/13200" in text


def test_doda_includes_viewer_tip():
    text = format_doda_results(_doda_result())
    assert "view_bild" in text


def _vigsel_result(**overrides) -> SearchResult:
    rec = {
        "postid": "789",
        "datum": "1875-06-20",
        "forsamling": "Uppsala",
        "lan": "Uppsala",
        "brudgum_fornamn": "Johan",
        "brudgum_efternamn": "Berg",
        "brudgum_yrke": "",
        "brudgum_alder": "",
        "brudgum_hemort": "",
        "brud_fornamn": "Maria",
        "brud_efternamn": "Svensson",
        "brud_yrke": "",
        "brud_alder": "",
        "brud_hemort": "",
        "anm": "",
        "referenskod": "SE/ULA/11800",
        "volym": "E I:2",
        "bild_id": "B0098765_00042",
    }
    rec.update(overrides)
    return SearchResult(records=[rec], total_hits=1, keyword="Johan", limit=25, offset=0)


def test_vigsel_includes_bild_id():
    text = format_vigsel_results(_vigsel_result())
    assert "Bild ID: B0098765_00042" in text


def test_vigsel_includes_ref():
    text = format_vigsel_results(_vigsel_result())
    assert "Ref: SE/ULA/11800" in text


def test_vigsel_includes_viewer_tip():
    text = format_vigsel_results(_vigsel_result())
    assert "view_bild" in text

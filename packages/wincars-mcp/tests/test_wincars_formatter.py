"""Tests for Wincars formatter — verifies archive/volume and viewer tip appear in output."""

from ra_mcp_wincars_lib.search_operations import SearchResult
from ra_mcp_wincars_mcp.formatter import format_wincars_results


def _wincars_result(**overrides) -> SearchResult:
    rec = {
        "nreg": "AC 1234",
        "typ": "PB",
        "fabrikat": "Volvo",
        "aar": "1952",
        "freg": "",
        "mreg": "",
        "treg": "",
        "cnr": "PV444-123456",
        "mnr": "B4B-78901",
        "status": "",
        "antag": "1952-05-10",
        "avreg": "",
        "hemvist": "Umeå",
        "anm": "",
        "arkivkod": "SE/HLA/1030038",
        "volym": "57",
    }
    rec.update(overrides)
    return SearchResult(records=[rec], total_hits=1, keyword="Volvo", limit=25, offset=0)


def test_wincars_includes_archive():
    text = format_wincars_results(_wincars_result())
    assert "Archive: SE/HLA/1030038" in text


def test_wincars_includes_volume():
    text = format_wincars_results(_wincars_result())
    assert "Volume: 57" in text


def test_wincars_includes_viewer_tip():
    text = format_wincars_results(_wincars_result())
    assert "view_document" in text


def test_wincars_omits_archive_when_empty():
    text = format_wincars_results(_wincars_result(arkivkod="", volym=""))
    assert "Archive:" not in text
    assert "Volume:" not in text

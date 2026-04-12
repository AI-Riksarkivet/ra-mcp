"""Tests for TORA formatter."""

from ra_mcp_tora_lib.models import ToraPlace
from ra_mcp_tora_mcp.formatter import format_tora_results


def _make_place(**overrides) -> ToraPlace:
    defaults = {
        "tora_id": "9809",
        "name": "Kerstinbo",
        "lat": 60.2506,
        "lon": 16.9486,
        "accuracy": "high",
        "parish": "Östervåla",
        "municipality": "Heby kommun",
        "county": "Uppsala län",
        "province": "Uppland",
    }
    defaults.update(overrides)
    return ToraPlace(**defaults)


def test_format_single_result():
    text = format_tora_results("Kerstinbo", [_make_place()])
    assert "Kerstinbo" in text
    assert "60.2506" in text
    assert "16.9486" in text
    assert "Östervåla" in text
    assert "Uppsala län" in text
    assert "https://data.riksarkivet.se/tora/9809" in text


def test_format_no_results():
    text = format_tora_results("Nonexistent", [])
    assert "No TORA places found" in text


def test_format_multiple_results():
    places = [
        _make_place(tora_id="1", name="Korbo", parish="A"),
        _make_place(tora_id="2", name="Korbo", parish="B"),
    ]
    text = format_tora_results("Korbo", places)
    assert "2 places" in text


def test_format_includes_wikidata_when_present():
    text = format_tora_results("Test", [_make_place(wikidata_url="https://www.wikidata.org/wiki/Q123")])
    assert "wikidata.org" in text


def test_format_omits_wikidata_when_empty():
    text = format_tora_results("Test", [_make_place(wikidata_url="")])
    assert "Wikidata" not in text

"""Tests for Sjömanshus formatter — verifies volume/page and viewer tip appear in output."""

from ra_mcp_sjomanshus_lib.search_operations import SearchResult
from ra_mcp_sjomanshus_mcp.formatter import format_liggare_results, format_matrikel_results


def _liggare_result(**overrides) -> SearchResult:
    rec = {
        "id": 1,
        "foernamn": "Karl",
        "efternamn1": "Johansson",
        "efternamn2": "",
        "foedelsedat": "1850-05-10",
        "foedelsefoers": "Karlskrona",
        "hemfoers": "Karlskrona",
        "befattning_yrke": "Matros",
        "sjoemanshus": "Karlskrona sjömanshus",
        "inskrivnr": "123",
        "fartyg": "Gefle",
        "typ": "Bark",
        "hemmahamn": "Karlskrona",
        "destination": "London",
        "kapten": "Svensson",
        "redare": "",
        "paamoenstort": "Karlskrona",
        "paamoenstdat": "1875-03-01",
        "avmoenstort": "London",
        "avmoenstdat": "1875-06-15",
        "arkiv": "Karlskrona sjömanshus",
        "arkivnr": "SE/LLA/10737",
        "volym": "DIa: 1",
        "sida": "31-32",
    }
    rec.update(overrides)
    return SearchResult(records=[rec], total_hits=1, keyword="Karl", limit=25, offset=0)


def test_liggare_includes_volume_and_page():
    text = format_liggare_results(_liggare_result())
    assert "Vol: DIa: 1" in text
    assert "Page: 31-32" in text


def test_liggare_includes_viewer_tip():
    text = format_liggare_results(_liggare_result())
    assert "view_document" in text


def test_liggare_omits_source_when_empty():
    text = format_liggare_results(_liggare_result(volym="", sida=""))
    assert "Source:" not in text


def _matrikel_result(**overrides) -> SearchResult:
    rec = {
        "id": 2,
        "foernamn": "Erik",
        "efternamn1": "Nilsson",
        "efternamn2": "",
        "foedelsedat": "1860-01-20",
        "foedelsefoers": "Göteborg",
        "hemfoers": "Göteborg",
        "far": "Nils Eriksson",
        "mor": "Anna Persdotter",
        "sjoemanshus": "Göteborgs sjömanshus",
        "inskrivnr": "456",
        "inskrivdat": "1878-04-10",
        "avfoerdort": "",
        "avfoerddat": "",
        "orsak": "",
        "arkiv": "Göteborgs sjömanshus",
        "arkivnr": "SE/GLA/10200",
        "volym": "AI: 5",
        "sida": "142",
    }
    rec.update(overrides)
    return SearchResult(records=[rec], total_hits=1, keyword="Erik", limit=25, offset=0)


def test_matrikel_includes_volume_and_page():
    text = format_matrikel_results(_matrikel_result())
    assert "Vol: AI: 5" in text
    assert "Page: 142" in text


def test_matrikel_includes_viewer_tip():
    text = format_matrikel_results(_matrikel_result())
    assert "view_document" in text

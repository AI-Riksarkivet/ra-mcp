"""Tests for TORA models."""

from ra_mcp_tora_lib.models import ToraPlace


def test_tora_place_construction():
    place = ToraPlace(
        tora_id="9809",
        name="Kerstinbo",
        lat=60.2506,
        lon=16.9486,
        accuracy="high",
        parish="Östervåla",
        municipality="Heby kommun",
        county="Uppsala län",
        province="Uppland",
    )
    assert place.name == "Kerstinbo"
    assert place.lat == 60.2506
    assert place.lon == 16.9486
    assert place.tora_url == "https://data.riksarkivet.se/tora/9809"


def test_tora_place_defaults():
    place = ToraPlace(tora_id="1", name="Test", lat=0.0, lon=0.0)
    assert place.accuracy == ""
    assert place.parish == ""
    assert place.wikidata_url == ""
    assert place.tora_url == "https://data.riksarkivet.se/tora/1"


def test_tora_place_from_sparql_binding():
    """Test parsing from a SPARQL result binding."""
    binding = {
        "place": {"value": "https://data.riksarkivet.se/tora/9809"},
        "name": {"value": "Kerstinbo"},
        "lat": {"value": "60,2506"},
        "long": {"value": "16,9486"},
        "accuracy": {"value": "https://data.riksarkivet.se/tora/coordinateaccuracy/high"},
        "parish": {"value": "Östervåla"},
        "municipality": {"value": "Heby kommun"},
        "county": {"value": "Uppsala län"},
        "province": {"value": "Uppland"},
        "wikidata": {"value": "https://www.wikidata.org/wiki/Q123"},
    }
    place = ToraPlace.from_sparql_binding(binding)
    assert place.tora_id == "9809"
    assert place.lat == 60.2506
    assert place.lon == 16.9486
    assert place.accuracy == "high"
    assert place.wikidata_url == "https://www.wikidata.org/wiki/Q123"


def test_tora_place_from_sparql_binding_missing_optional():
    """Optional fields default to empty string."""
    binding = {
        "place": {"value": "https://data.riksarkivet.se/tora/100"},
        "name": {"value": "Testby"},
        "lat": {"value": "58,0"},
        "long": {"value": "15,0"},
    }
    place = ToraPlace.from_sparql_binding(binding)
    assert place.parish == ""
    assert place.wikidata_url == ""
    assert place.accuracy == ""

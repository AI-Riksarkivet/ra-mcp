"""Tests for TORA SPARQL client."""

from unittest.mock import AsyncMock

import pytest

from ra_mcp_tora_lib.client import ToraClient


def _mock_sparql_response(bindings: list[dict]) -> dict:
    """Build a SPARQL JSON response."""
    return {"results": {"bindings": bindings}}


def _kerstinbo_binding() -> dict:
    return {
        "place": {"value": "https://data.riksarkivet.se/tora/9809"},
        "name": {"value": "Kerstinbo"},
        "lat": {"value": "60,2506"},
        "long": {"value": "16,9486"},
        "accuracy": {"value": "https://data.riksarkivet.se/tora/coordinateaccuracy/high"},
        "parish": {"value": "Östervåla"},
        "municipality": {"value": "Heby kommun"},
        "county": {"value": "Uppsala län"},
        "province": {"value": "Uppland"},
    }


@pytest.fixture
def mock_sparql():
    return AsyncMock()


async def test_search_returns_places(mock_sparql):
    # Three calls: place search, image search, map search
    mock_sparql.side_effect = [
        _mock_sparql_response([_kerstinbo_binding()]),
        _mock_sparql_response([]),
        _mock_sparql_response([]),
    ]
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo")

    assert len(results) == 1
    assert results[0].name == "Kerstinbo"
    assert results[0].lat == 60.2506
    assert mock_sparql.call_count == 3


async def test_search_empty_results(mock_sparql):
    mock_sparql.return_value = _mock_sparql_response([])
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Nonexistent")

    assert results == []


async def test_search_with_parish_filter(mock_sparql):
    mock_sparql.side_effect = [
        _mock_sparql_response([_kerstinbo_binding()]),
        _mock_sparql_response([]),
        _mock_sparql_response([]),
    ]
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo", parish="Östervåla")

    assert len(results) == 1
    # Verify the first SPARQL query (place search) included a parish filter
    first_call_query = mock_sparql.call_args_list[0][0][0]
    assert "Östervåla" in first_call_query


async def test_search_endpoint_down(mock_sparql):
    mock_sparql.return_value = None
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo")

    assert results == []


async def test_search_deduplicates(mock_sparql):
    """TORA often returns duplicate bindings — client should deduplicate."""
    binding = _kerstinbo_binding()
    mock_sparql.side_effect = [
        _mock_sparql_response([binding, binding]),
        _mock_sparql_response([]),
        _mock_sparql_response([]),
    ]
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo")

    assert len(results) == 1


async def test_search_returns_images(mock_sparql):
    """Places with linked Suecia images should have them populated."""
    img_binding = {
        "place": {"value": "https://data.riksarkivet.se/tora/9809"},
        "imgTitle": {"value": "Boråås"},
        "imgUrl": {"value": "https://weburn.kb.se/suecia/bild/20/8465620.jpg"},
        "imgLibris": {"value": "https://libris.kb.se/bib/8465620"},
        "imgCreator": {"value": "Aveelen, Johannes van den,"},
        "imgPeriod": {"value": "[168-]"},
    }
    mock_sparql.side_effect = [
        _mock_sparql_response([_kerstinbo_binding()]),
        _mock_sparql_response([img_binding]),
        _mock_sparql_response([]),
    ]
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo")

    assert len(results) == 1
    assert len(results[0].images) == 1
    assert results[0].images[0].title == "Boråås"
    assert "weburn.kb.se" in results[0].images[0].image_url

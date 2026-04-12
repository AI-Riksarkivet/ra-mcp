"""Tests for TORA SPARQL client."""

import pytest
from unittest.mock import AsyncMock

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
    mock_sparql.return_value = _mock_sparql_response([_kerstinbo_binding()])
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo")

    assert len(results) == 1
    assert results[0].name == "Kerstinbo"
    assert results[0].lat == 60.2506
    mock_sparql.assert_called_once()


async def test_search_empty_results(mock_sparql):
    mock_sparql.return_value = _mock_sparql_response([])
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Nonexistent")

    assert results == []


async def test_search_with_parish_filter(mock_sparql):
    mock_sparql.return_value = _mock_sparql_response([_kerstinbo_binding()])
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo", parish="Östervåla")

    assert len(results) == 1
    # Verify the SPARQL query included a parish filter
    query_arg = mock_sparql.call_args[0][0]
    assert "Östervåla" in query_arg


async def test_search_endpoint_down(mock_sparql):
    mock_sparql.return_value = None
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo")

    assert results == []


async def test_search_deduplicates(mock_sparql):
    """TORA often returns duplicate bindings — client should deduplicate."""
    binding = _kerstinbo_binding()
    mock_sparql.return_value = _mock_sparql_response([binding, binding])
    client = ToraClient(sparql_fn=mock_sparql)

    results = await client.search("Kerstinbo")

    assert len(results) == 1

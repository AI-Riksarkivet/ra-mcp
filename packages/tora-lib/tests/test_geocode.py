"""Tests for the geocode convenience function."""

from unittest.mock import AsyncMock, patch

from ra_mcp_tora_lib.geocode import geocode
from ra_mcp_tora_lib.models import ToraPlace


def _make_place(**overrides) -> ToraPlace:
    defaults = {"tora_id": "1", "name": "Test", "lat": 60.0, "lon": 16.0, "accuracy": "high"}
    defaults.update(overrides)
    return ToraPlace(**defaults)


@patch("ra_mcp_tora_lib.geocode.ToraClient")
async def test_geocode_returns_coordinates(mock_cls):
    client = AsyncMock()
    client.search.return_value = [_make_place(lat=60.25, lon=16.95)]
    mock_cls.return_value = client

    result = await geocode("Kerstinbo")

    assert result == (60.25, 16.95)


@patch("ra_mcp_tora_lib.geocode.ToraClient")
async def test_geocode_returns_none_when_not_found(mock_cls):
    client = AsyncMock()
    client.search.return_value = []
    mock_cls.return_value = client

    result = await geocode("Nonexistent")

    assert result is None


@patch("ra_mcp_tora_lib.geocode.ToraClient")
async def test_geocode_passes_parish_and_county(mock_cls):
    client = AsyncMock()
    client.search.return_value = [_make_place()]
    mock_cls.return_value = client

    await geocode("Korbo", parish="Östervåla", county="Uppsala")

    client.search.assert_called_once_with("Korbo", parish="Östervåla", county="Uppsala")

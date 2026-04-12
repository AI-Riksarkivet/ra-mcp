"""Integration tests against live TORA SPARQL endpoint.

These tests require network access. Skip with: pytest -m "not integration"
"""

import pytest

from ra_mcp_tora_lib.client import ToraClient
from ra_mcp_tora_lib.geocode import geocode


pytestmark = pytest.mark.integration


async def test_live_search_kerstinbo():
    """Kerstinbo should be findable and have coordinates."""
    client = ToraClient()
    results = await client.search("Kerstinbo")

    assert len(results) >= 1
    place = results[0]
    assert place.name == "Kerstinbo"
    assert 59 < place.lat < 61  # roughly Uppsala county
    assert 16 < place.lon < 18


async def test_live_search_lund():
    """Lund — a well-known settlement, should return multiple matches."""
    client = ToraClient()
    results = await client.search("Lund")

    assert len(results) >= 1
    assert 55 < results[0].lat < 65  # somewhere in Sweden


async def test_live_geocode():
    """geocode() should return a tuple."""
    result = await geocode("Kerstinbo")

    assert result is not None
    lat, _lon = result
    assert 59 < lat < 61


async def test_live_geocode_not_found():
    result = await geocode("Xyzzyplansen")

    assert result is None

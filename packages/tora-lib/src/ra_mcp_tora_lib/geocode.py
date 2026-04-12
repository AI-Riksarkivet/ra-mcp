"""Convenience geocode function for looking up coordinates by place name."""

from __future__ import annotations

from ra_mcp_common.http_client import default_http_client

from .client import ToraClient


async def geocode(
    name: str,
    parish: str | None = None,
    county: str | None = None,
) -> tuple[float, float] | None:
    """Look up coordinates for a historical Swedish place name.

    Args:
        name: Place name to search for (exact match).
        parish: Optional parish name to disambiguate.
        county: Optional county name to disambiguate.

    Returns:
        (lat, lon) tuple for the best match, or None if not found.
    """
    client = ToraClient(http_client=default_http_client)
    places = await client.search(name, parish=parish, county=county)
    if not places:
        return None
    return (places[0].lat, places[0].lon)

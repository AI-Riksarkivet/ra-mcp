"""MCP tool for searching TORA historical places."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_tora_lib.client import ToraClient

from .formatter import format_tora_results


logger = logging.getLogger("ra_mcp.tora.tora_tool")


def register_tora_tool(mcp) -> None:
    """Register the search_tora MCP tool."""

    @mcp.tool(
        name="search_tora",
        tags={"tora", "geography", "geocode", "places", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Geocode historical Swedish places using TORA (Topografiskt register på Riksarkivet). "
            "Returns WGS84 coordinates, parish, municipality, county, and province for 51,000 settlements. "
            "Many places include linked historical Suecia Antiqua engravings (1600s) from KB. "
            "Use to find the location of a historical Swedish place, village, or settlement. "
            "Optionally filter by parish or county to disambiguate common place names. "
            "When presenting results: show the location on a map using the coordinates, "
            "and use view_document_urls to display linked historical images in the document viewer "
            "(pass image URLs as image_urls, empty strings as text_layer_urls)."
        ),
    )
    async def search_tora(
        name: Annotated[
            str,
            Field(description="Place name to search for (exact match, e.g. 'Kerstinbo', 'Abbekås')."),
        ],
        parish: Annotated[
            str | None,
            Field(description="Optional parish name to disambiguate (case-insensitive substring match)."),
        ] = None,
        county: Annotated[
            str | None,
            Field(description="Optional county/län to disambiguate (case-insensitive substring match, e.g. 'Uppsala', 'Malmöhus')."),
        ] = None,
    ) -> str:
        """Search for a historical Swedish place and get its coordinates."""
        if not name or not name.strip():
            return "Error: name must not be empty."

        logger.info("search_tora called with name='%s', parish=%s, county=%s", name, parish, county)

        try:
            client = ToraClient()
            places = await client.search(name.strip(), parish=parish, county=county)
            return format_tora_results(name, places)

        except Exception as exc:
            logger.error("search_tora failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: TORA search failed — {exc!s}"

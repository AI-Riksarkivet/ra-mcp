"""TORA SPARQL client — queries historical settlements from Riksarkivet."""

from __future__ import annotations

import json
import logging

import httpx

from .config import SPARQL_ENDPOINT
from .models import ToraPlace


logger = logging.getLogger("ra_mcp.tora.client")


def _build_search_query(name: str, parish: str | None = None, county: str | None = None) -> str:
    """Build SPARQL query to find settlements by name with optional filters."""
    filters = [f'FILTER(LCASE(?name) = LCASE("{name}"))']
    if parish:
        filters.append(f'FILTER(CONTAINS(LCASE(?parish), LCASE("{parish}")))')
    if county:
        filters.append(f'FILTER(CONTAINS(LCASE(?county), LCASE("{county}")))')

    filter_block = "\n    ".join(filters)

    return f"""
PREFIX tora: <https://data.riksarkivet.se/tora/schema/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?place ?name ?lat ?long ?accuracy ?parish ?municipality ?county ?province ?wikidata WHERE {{
  ?place a tora:HistoricalSettlementUnit ;
         skos:prefLabel ?name ;
         geo:lat ?lat ;
         geo:long ?long .
  {filter_block}
  OPTIONAL {{ ?place dct:coverage ?accuracy }}
  OPTIONAL {{ ?place tora:modernParish ?parishUri . ?parishUri skos:prefLabel ?parish }}
  OPTIONAL {{ ?place tora:modernMunicipality ?munUri . ?munUri skos:prefLabel ?municipality }}
  OPTIONAL {{ ?place tora:modernCounty ?countyUri . ?countyUri skos:prefLabel ?county }}
  OPTIONAL {{ ?place tora:province_name ?province }}
  OPTIONAL {{ ?place rdfs:seeAlso ?wikidata . FILTER(CONTAINS(STR(?wikidata), "wikidata")) }}
}} LIMIT 20
"""


async def _sparql_post(query: str) -> dict | None:
    """Execute a SPARQL query via POST and return parsed JSON.

    The TORA endpoint only returns JSON for POST requests with
    application/x-www-form-urlencoded encoding.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            SPARQL_ENDPOINT,
            data={"query": query},
            headers={
                "Accept": "application/sparql-results+json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        if response.status_code != 200:
            logger.error("TORA SPARQL returned %d", response.status_code)
            return None
        return json.loads(response.content)


class ToraClient:
    """Client for querying TORA settlements via SPARQL."""

    def __init__(self, sparql_fn=_sparql_post) -> None:
        self._sparql = sparql_fn

    async def search(
        self,
        name: str,
        parish: str | None = None,
        county: str | None = None,
    ) -> list[ToraPlace]:
        """Search for settlements by name, optionally filtered by parish/county."""
        query = _build_search_query(name, parish, county)

        try:
            data = await self._sparql(query)
        except Exception as e:
            logger.error("TORA SPARQL query failed: %s", e)
            return []

        if not data:
            return []

        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return []

        # Deduplicate by tora_id (SPARQL often returns duplicate rows)
        seen: set[str] = set()
        places: list[ToraPlace] = []
        for binding in bindings:
            try:
                place = ToraPlace.from_sparql_binding(binding)
            except Exception as e:
                logger.warning("Failed to parse TORA binding: %s", e)
                continue
            if place.tora_id not in seen:
                seen.add(place.tora_id)
                places.append(place)

        # Sort by accuracy: high > medium > low > empty
        accuracy_order = {"high": 0, "medium": 1, "low": 2, "": 3}
        places.sort(key=lambda p: accuracy_order.get(p.accuracy, 3))

        return places

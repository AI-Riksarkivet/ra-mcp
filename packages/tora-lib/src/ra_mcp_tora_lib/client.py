"""TORA SPARQL client — queries historical settlements from Riksarkivet."""

from __future__ import annotations

import json
import logging

import httpx

from .config import SPARQL_ENDPOINT
from .models import ToraImage, ToraPlace


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


def _build_images_query(tora_ids: list[str]) -> str:
    """Build SPARQL query to fetch linked Suecia images for given place IDs."""
    uris = " ".join(f"<https://data.riksarkivet.se/tora/{tid}>" for tid in tora_ids)
    return f"""
PREFIX tora: <https://data.riksarkivet.se/tora/schema/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX schema: <http://schema.org/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>

SELECT DISTINCT ?place ?imgTitle ?imgUrl ?imgLibris ?imgCreator ?imgPeriod WHERE {{
  VALUES ?place {{ {uris} }}
  ?dsm a tora:DigitizedSourceMaterial ;
       dct:references ?place ;
       skos:prefLabel ?imgTitle ;
       schema:image ?imgUrl .
  FILTER(CONTAINS(STR(?imgUrl), ".jpg"))
  OPTIONAL {{ ?dsm dct:source ?imgLibris }}
  OPTIONAL {{ ?dsm dc:creator ?imgCreator }}
  OPTIONAL {{ ?dsm dct:description ?imgPeriod }}
}}
"""


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

        # Fetch linked images for all found places
        if places:
            await self._enrich_with_images(places)

        return places

    async def _enrich_with_images(self, places: list[ToraPlace]) -> None:
        """Fetch linked Suecia images and attach to places."""
        tora_ids = [p.tora_id for p in places]
        query = _build_images_query(tora_ids)

        try:
            data = await self._sparql(query)
        except Exception as e:
            logger.warning("TORA image query failed: %s", e)
            return

        if not data:
            return

        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return

        # Group images by place URI
        place_map = {p.tora_id: p for p in places}
        seen_images: set[str] = set()

        for binding in bindings:
            place_uri = binding.get("place", {}).get("value", "")
            tora_id = place_uri.rsplit("/", 1)[-1] if "/" in place_uri else ""
            img_url = binding.get("imgUrl", {}).get("value", "")

            # Deduplicate by image URL per place
            dedup_key = f"{tora_id}:{img_url}"
            if dedup_key in seen_images:
                continue
            seen_images.add(dedup_key)

            if tora_id in place_map:
                try:
                    image = ToraImage.from_sparql_binding(binding)
                    place_map[tora_id].images.append(image)
                except Exception as e:
                    logger.warning("Failed to parse TORA image binding: %s", e)

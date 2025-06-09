from typing import Dict, List, Optional
from urllib.parse import urlencode

from oxenstierna.ra_api.models.search_model import (
    SearchResults,
    ObjectType,
    SortOption,
    Provenance,
)
from oxenstierna.ra_api.base_client import ApiClientError, BaseRiksarkivetClient


class RiksarkivetSearchClient(BaseRiksarkivetClient):
    """Client for searching Riksarkivet records database."""

    def __init__(
        self,
        search_api_base_url: str = "https://data.riksarkivet.se/api",
    ):
        """
        Initialize the search client.

        Args:
            search_api_base_url: Base URL for Search API (default: Riksarkivet URL)
        """
        self.search_api_base_url = search_api_base_url

    async def search_records(
        self,
        text: Optional[str] = None,
        name: Optional[str] = None,
        place: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        object_type: Optional[ObjectType] = None,
        record_type: Optional[str] = None,
        provenance: Optional[Provenance] = None,
        archival_institution: Optional[str] = None,
        place_filter: Optional[str] = None,
        custom_facets: Optional[Dict[str, str]] = None,
        sort: SortOption = SortOption.RELEVANCE,
        offset: int = 0,
        max_results: int = 100,
    ) -> SearchResults:
        """
        Search the Riksarkivet records database.

        Args:
            text: General free text search
            name: Free text search on name/title
            place: Free text search on referenced place name
            year_min: Earliest year to include
            year_max: Latest year to include
            object_type: Filter by object type (RecordSet, Record, Agent, Topography)
            record_type: Filter by specific record type (Volume, Dossier, etc.)
            provenance: Filter by provenance category
            archival_institution: Filter by holding institution
            place_filter: Filter by hierarchical place (e.g., "Sverige/Stockholms län")
            custom_facets: Additional facet filters as dict {facet_name: value}
            sort: Sort order (default: relevance)
            offset: Pagination offset (default: 0)
            max_results: Maximum results to return (default: 100)

        Returns:
            SearchResults containing matching records with PIDs and facets
        """
        params = {}

        if text:
            params["text"] = text
        if name:
            params["name"] = name
        if place:
            params["place"] = place

        if year_min:
            params["year_min"] = str(year_min)
        if year_max:
            params["year_max"] = str(year_max)

        facet_filters = []

        if object_type:
            facet_filters.append(f"ObjectType:{object_type.value}")
        if record_type:
            facet_filters.append(f"Type:{record_type}")
        if provenance:
            facet_filters.append(f"Provenance:{provenance.value}")
        if archival_institution:
            facet_filters.append(f"ArchivalInstitution:{archival_institution}")
        if place_filter:
            facet_filters.append(f"Place:{place_filter}")

        if custom_facets:
            for facet_name, facet_value in custom_facets.items():
                facet_filters.append(f"{facet_name}:{facet_value}")

        if facet_filters:
            params["facet"] = ";".join(facet_filters)

        params["sort"] = sort.value
        params["offset"] = str(offset)
        params["max"] = str(max_results)

        query_string = urlencode(params, safe=":;")
        url = f"{self.search_api_base_url}/records?{query_string}"

        response = await self._make_request(url)

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise ApiClientError(f"Unexpected content type for search: {content_type}")

        search_data = response.json()

        query_parts = []
        if text:
            query_parts.append(f"text:'{text}'")
        if name:
            query_parts.append(f"name:'{name}'")
        if place:
            query_parts.append(f"place:'{place}'")
        if year_min or year_max:
            year_range = f"{year_min or '?'}-{year_max or '?'}"
            query_parts.append(f"years:{year_range}")
        if facet_filters:
            query_parts.append(f"filters:{len(facet_filters)}")

        query_description = " | ".join(query_parts) if query_parts else "all records"

        return SearchResults.from_api_response(query_description, search_data)

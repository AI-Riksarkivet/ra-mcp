from oxenstierna.ra_api.api_models import (
    SearchResults,
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
        self, query: str, only_digitized: bool = True, offset: int = 0, limit: int = 100
    ) -> SearchResults:
        """
        Search the Riksarkivet records database.

        Args:
            query: Search terms (e.g., "coffee", "medical records")
            only_digitized: Only return digitized materials (default: True)
            offset: Pagination offset (default: 0)
            limit: Maximum results to return (default: 100)

        Returns:
            SearchResults containing matching records with PIDs
        """
        params = {"text": query, "offset": offset}

        if only_digitized:
            params["only_digitised_materials"] = "true"

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.search_api_base_url}/records?{query_string}"

        response = await self._make_request(url)

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise ApiClientError(f"Unexpected content type for search: {content_type}")

        search_data = response.json()
        return SearchResults.from_api_response(query, search_data)

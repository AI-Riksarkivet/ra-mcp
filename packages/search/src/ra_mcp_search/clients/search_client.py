"""
Search API client for Riksarkivet.

Provides a simplified interface to the Riksarkivet Search API (/api/records endpoint)
with direct Pydantic response parsing.
"""

import logging
from typing import Optional

from ra_mcp_common.utils.http_client import HTTPClient

from ra_mcp_search.config import SEARCH_API_BASE_URL, REQUEST_TIMEOUT, DEFAULT_MAX_RESULTS
from ra_mcp_search.models import RecordsResponse


class SearchAPI:
    """
    Client for Riksarkivet Search API.

    Handles searching transcribed documents and returns structured responses
    that directly map to the API's JSON structure.
    """

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client
        self.logger = logging.getLogger("ra_mcp.search_api")

    def search(
        self,
        text: Optional[str] = None,
        transcribed_text: Optional[str] = None,
        only_digitised_materials: bool = True,
        max: int = DEFAULT_MAX_RESULTS,
        offset: int = 0,
        max_snippets_per_record: Optional[int] = None,
        sort: str = "relevance",
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        name: Optional[str] = None,
        place: Optional[str] = None,
    ) -> RecordsResponse:
        """
        Search for records using various search parameters.

        Parameter names match the Search API specification for clarity.
        You can search either transcribed materials or general text (metadata, names, places).

        Args:
            text: General free-text search across all fields
            transcribed_text: Search specifically in AI-transcribed text (requires only_digitised_materials=True)
            only_digitised_materials: Limit results to digitized materials (default: True)
            max: Maximum number of records to return (API parameter name)
            offset: Pagination offset (API parameter name)
            max_snippets_per_record: Client-side snippet limiting per record (not sent to API)
            sort: Sort order — one of: relevance, timeAsc, timeDesc, alphaAsc, alphaDesc
            year_min: Filter results to this start year or later
            year_max: Filter results to this end year or earlier
            name: Search by person name (API field, can combine with text)
            place: Search by place name (API field, can combine with text)

        Returns:
            RecordsResponse with all API fields populated

        Raises:
            ValueError: If transcribed_text is used without only_digitised_materials=True
        """
        # Validate parameters
        if transcribed_text and not only_digitised_materials:
            raise ValueError(
                "transcribed_text search requires only_digitised_materials=True. Use text parameter instead of transcribed_text to search all materials."
            )

        if not text and not transcribed_text and not name and not place:
            raise ValueError("Must provide at least one search parameter: 'text', 'transcribed_text', 'name', or 'place'")

        search_term = transcribed_text or text
        search_type = "transcribed" if transcribed_text else "general"
        self.logger.info(f"Starting {search_type} search: keyword='{search_term}', max={max}, offset={offset}")

        try:
            # Build search parameters
            params = {
                "max": max,
                "offset": offset,
                "sort": sort,
            }

            if only_digitised_materials:
                params["only_digitised_materials"] = "true"

            if transcribed_text:
                params["transcribed_text"] = transcribed_text
            elif text:
                params["text"] = text

            if name:
                params["name"] = name
            if place:
                params["place"] = place
            if year_min is not None:
                params["year_min"] = year_min
            if year_max is not None:
                params["year_max"] = year_max

            response_data = self.http_client.get_json(SEARCH_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)

            # Parse entire API response with Pydantic
            response = RecordsResponse(**response_data)

            # Apply client-side snippet limiting if requested
            if max_snippets_per_record:
                self._limit_snippets(response, max_snippets_per_record)

            self.logger.info(f"✓ Search completed: {response.count_snippets()} snippets from {len(response.items)} records ({response.total_hits} total)")

            return response

        except Exception as error:
            self.logger.error(f"✗ Search failed: {type(error).__name__}: {error}")
            raise

    def search_transcribed_text(
        self,
        transcribed_text: str,
        max: int = DEFAULT_MAX_RESULTS,
        offset: int = 0,
        max_snippets_per_record: Optional[int] = None,
    ) -> RecordsResponse:
        """
        Search for keyword in transcribed materials (convenience method).

        This is a convenience wrapper around the main search() method.

        Args:
            transcribed_text: Search term or Solr query (API parameter name)
            max: Maximum number of records to return (API parameter name)
            offset: Pagination offset (API parameter name)
            max_snippets_per_record: Client-side snippet limiting per record (not sent to API)

        Returns:
            RecordsResponse with all API fields populated
        """
        return self.search(
            transcribed_text=transcribed_text, only_digitised_materials=True, max=max, offset=offset, max_snippets_per_record=max_snippets_per_record
        )

    def _limit_snippets(self, response: RecordsResponse, max_snippets: int) -> None:
        """
        Limit snippets per record (client-side truncation).

        Modifies the response in-place to keep only the first N snippets per record.
        """
        for record in response.items:
            if record.transcribed_text:
                record.transcribed_text.snippets = record.transcribed_text.snippets[:max_snippets]

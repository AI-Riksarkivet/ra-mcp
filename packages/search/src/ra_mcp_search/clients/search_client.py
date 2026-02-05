"""
Search API client for Riksarkivet.

Provides a simplified interface to the Riksarkivet Search API (/api/records endpoint)
with direct Pydantic response parsing.
"""

import logging
from typing import Optional

from ra_mcp_core.utils.http_client import HTTPClient

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

    def search_transcribed_text(
        self,
        transcribed_text: str,
        max: int = DEFAULT_MAX_RESULTS,
        offset: int = 0,
        max_snippets_per_record: Optional[int] = None,
    ) -> RecordsResponse:
        """
        Search for keyword in transcribed materials.

        Parameter names match the Search API specification for clarity.

        Args:
            transcribed_text: Search term or Solr query (API parameter name)
            max: Maximum number of records to return (API parameter name)
            offset: Pagination offset (API parameter name)
            max_snippets_per_record: Client-side snippet limiting per record (not sent to API)

        Returns:
            RecordsResponse with all API fields populated
        """
        self.logger.info(f"Starting search: keyword='{transcribed_text}', max={max}, offset={offset}")

        try:
            # Execute search request
            params = {
                "transcribed_text": transcribed_text,
                "only_digitised_materials": "true",
                "max": max,
                "offset": offset,
                "sort": "relevance",
            }

            response_data = self.http_client.get_json(
                SEARCH_API_BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )

            # Parse entire API response with Pydantic
            response = RecordsResponse(**response_data)

            # Apply client-side snippet limiting if requested
            if max_snippets_per_record:
                self._limit_snippets(response, max_snippets_per_record)

            self.logger.info(
                f"✓ Search completed: {response.count_snippets()} snippets "
                f"from {len(response.items)} records ({response.total_hits} total)"
            )

            return response

        except Exception as error:
            self.logger.error(f"✗ Search failed: {type(error).__name__}: {error}")
            raise

    def _limit_snippets(self, response: RecordsResponse, max_snippets: int) -> None:
        """
        Limit snippets per record (client-side truncation).

        Modifies the response in-place to keep only the first N snippets per record.
        """
        for record in response.items:
            if record.transcribed_text:
                record.transcribed_text.snippets = record.transcribed_text.snippets[:max_snippets]

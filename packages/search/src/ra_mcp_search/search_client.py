"""
Search API client for Riksarkivet.

Provides a simplified interface to the Riksarkivet Search API (/api/records endpoint)
with direct Pydantic response parsing.
"""

import logging

from opentelemetry.trace import StatusCode

from ra_mcp_common.telemetry import get_tracer
from ra_mcp_common.utils.http_client import HTTPClient
from ra_mcp_search.config import DEFAULT_MAX_RESULTS, REQUEST_TIMEOUT, SEARCH_API_BASE_URL
from ra_mcp_search.models import RecordsResponse


_tracer = get_tracer("ra_mcp.search_api")


class SearchClient:
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
        text: str | None = None,
        transcribed_text: str | None = None,
        only_digitised_materials: bool = True,
        max_results: int = DEFAULT_MAX_RESULTS,
        offset: int = 0,
        max_snippets_per_record: int | None = None,
        sort: str = "relevance",
        year_min: int | None = None,
        year_max: int | None = None,
        name: str | None = None,
        place: str | None = None,
    ) -> RecordsResponse:
        """
        Search for records using various search parameters.

        Parameter names match the Search API specification for clarity.
        You can search either transcribed materials or general text (metadata, names, places).

        Args:
            text: General free-text search across all fields
            transcribed_text: Search specifically in AI-transcribed text (requires only_digitised_materials=True)
            only_digitised_materials: Limit results to digitized materials (default: True)
            max_results: Maximum number of records to return
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
        self.logger.info("Starting %s search: keyword='%s', max=%d, offset=%d", search_type, search_term, max_results, offset)

        with _tracer.start_as_current_span(
            "SearchClient.search",
            attributes={
                "search.type": search_type,
                "search.keyword": search_term or "",
                "search.offset": offset,
                "search.max_results": max_results,
            },
        ) as span:
            try:
                # Build search parameters
                params = {
                    "max": max_results,
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

                self.logger.info(
                    "✓ Search completed: %d snippets from %d records (%d total)", response.count_snippets(), len(response.items), response.total_hits
                )

                span.set_attribute("search.total_hits", response.total_hits)
                span.set_attribute("search.result_count", len(response.items))
                return response

            except Exception as error:
                span.set_status(StatusCode.ERROR, str(error))
                span.record_exception(error)
                self.logger.error("✗ Search failed: %s: %s", type(error).__name__, error)
                raise

    def search_transcribed_text(
        self,
        transcribed_text: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        offset: int = 0,
        max_snippets_per_record: int | None = None,
    ) -> RecordsResponse:
        """
        Search for keyword in transcribed materials (convenience method).

        This is a convenience wrapper around the main search() method.

        Args:
            transcribed_text: Search term or Solr query (API parameter name)
            max_results: Maximum number of records to return
            offset: Pagination offset (API parameter name)
            max_snippets_per_record: Client-side snippet limiting per record (not sent to API)

        Returns:
            RecordsResponse with all API fields populated
        """
        return self.search(
            transcribed_text=transcribed_text,
            only_digitised_materials=True,
            max_results=max_results,
            offset=offset,
            max_snippets_per_record=max_snippets_per_record,
        )

    def _limit_snippets(self, response: RecordsResponse, max_snippets: int) -> None:
        """
        Limit snippets per record (client-side truncation).

        Modifies the response in-place to keep only the first N snippets per record.
        """
        for record in response.items:
            if record.transcribed_text:
                record.transcribed_text.snippets = record.transcribed_text.snippets[:max_snippets]

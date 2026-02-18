"""
Search operations that can be used by both CLI and MCP interfaces.
Handles keyword searching.
"""

from opentelemetry.trace import StatusCode

from ra_mcp_common.telemetry import get_meter, get_tracer
from ra_mcp_common.utils.http_client import HTTPClient

from .search_client import SearchAPI
from .models import SearchResult


_tracer = get_tracer("ra_mcp.search_operations")
_meter = get_meter("ra_mcp.search_operations")
_search_counter = _meter.create_counter("ra_mcp.search.requests", description="Search operations executed")
_results_histogram = _meter.create_histogram("ra_mcp.search.results", description="Number of results returned per search")


class SearchOperations:
    """Search operations for Riksarkivet document collections.

    Provides keyword search functionality.

    Attributes:
        search_api: Client for executing text searches.
    """

    def __init__(self, http_client: HTTPClient):
        self.search_api = SearchAPI(http_client=http_client)

    def search(
        self,
        keyword: str,
        transcribed_only: bool = True,
        only_digitised: bool = True,
        offset: int = 0,
        max_results: int = 10,
        max_snippets_per_record: int | None = None,
        sort: str = "relevance",
        year_min: int | None = None,
        year_max: int | None = None,
        name: str | None = None,
        place: str | None = None,
    ) -> SearchResult:
        """Search for records in document collections.

        Executes a keyword search across Riksarkivet collections. Can search either
        transcribed text specifically or general metadata (titles, names, places, etc.).

        Args:
            keyword: Search term or phrase to look for.
            transcribed_only: If True, search in transcribed text only. If False, search all fields.
            only_digitised: Limit results to digitized materials (default: True).
            offset: Number of results to skip for pagination.
            max_results: Maximum number of documents to return.
            max_snippets_per_record: Limit snippets per document (None for unlimited).
            sort: Sort order — one of: relevance, timeAsc, timeDesc, alphaAsc, alphaDesc.
            year_min: Filter results to this start year or later.
            year_max: Filter results to this end year or earlier.
            name: Search by person name (can combine with keyword).
            place: Search by place name (can combine with keyword).

        Returns:
            SearchResult containing documents, total count, and metadata.
        """
        search_type = "transcribed" if transcribed_only else "metadata"
        with _tracer.start_as_current_span(
            "SearchOperations.search",
            attributes={
                "search.keyword": keyword,
                "search.transcribed_only": transcribed_only,
                "search.offset": offset,
                "search.max_results": max_results,
            },
        ) as span:
            try:
                # Execute search using API parameter names
                response = self.search_api.search(
                    transcribed_text=keyword if transcribed_only else None,
                    text=keyword if not transcribed_only else None,
                    only_digitised_materials=only_digitised,
                    max_results=max_results,
                    offset=offset,
                    max_snippets_per_record=max_snippets_per_record,
                    sort=sort,
                    year_min=year_min,
                    year_max=year_max,
                    name=name,
                    place=place,
                )

                span.set_attribute("search.total_hits", response.total_hits)
                _search_counter.add(1, {"search.type": search_type, "search.status": "success"})
                _results_histogram.record(response.total_hits, {"search.type": search_type})
                return SearchResult(
                    response=response, transcribed_text=keyword, max=max_results, offset=offset, max_snippets_per_record=max_snippets_per_record
                )
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                _search_counter.add(1, {"search.type": search_type, "search.status": "error"})
                raise

    def search_transcribed(
        self,
        keyword: str,
        offset: int = 0,
        max_results: int = 10,
        max_snippets_per_record: int | None = None,
    ) -> SearchResult:
        """Search for transcribed text across document collections (convenience method).

        Executes a keyword search across all transcribed documents in the Riksarkivet
        collections. This is a convenience wrapper around the main search() method.

        Args:
            keyword: Search term or phrase to look for in transcribed text.
            offset: Number of results to skip for pagination.
            max_results: Maximum number of documents to return.
            max_snippets_per_record: Limit snippets per document (None for unlimited).

        Returns:
            SearchResult containing documents, total count, and metadata.
        """
        return self.search(
            keyword=keyword, transcribed_only=True, only_digitised=True, offset=offset, max_results=max_results, max_snippets_per_record=max_snippets_per_record
        )

"""
Search operations that can be used by both CLI and MCP interfaces.
Handles keyword searching and result enrichment.
"""

from typing import Optional

from ..clients import SearchAPI
from ..models import SearchResult
from .search_enrichment_service import SearchEnrichmentService
from ..utils.http_client import HTTPClient


class SearchOperations:
    """Search operations for Riksarkivet document collections.

    Provides keyword search functionality with optional context enrichment.

    Attributes:
        search_api: Client for executing text searches.
        enrichment_service: Service for enriching search results with context.
    """

    def __init__(self, http_client: HTTPClient):
        self.search_api = SearchAPI(http_client=http_client)
        self.enrichment_service = SearchEnrichmentService(http_client=http_client)

    def search_transcribed(
        self,
        keyword: str,
        offset: int = 0,
        max_results: int = 10,
        max_hits_per_document: Optional[int] = None,
        show_context: bool = False,
        max_pages_with_context: int = 0,
    ) -> SearchResult:
        """Search for transcribed text across document collections.

        Executes a keyword search across all transcribed documents in the Riksarkivet
        collections and optionally enriches results with surrounding context.

        Args:
            keyword: Search term or phrase to look for in transcribed text.
            offset: Number of results to skip for pagination.
            max_results: Maximum number of documents to return.
            max_hits_per_document: Limit hits per document (None for unlimited).
            show_context: Whether to fetch and include surrounding text context.
            max_pages_with_context: Number of pages to enrich with full context.

        Returns:
            SearchResult containing search hits, total count, and metadata.
            If show_context is True, hits will include enriched page content.
        """
        # Execute search and build operation in one step
        hits, total_hits = self.search_api.search_transcribed_text(keyword, max_results, offset, max_hits_per_document)

        search_result = SearchResult(
            hits=hits,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            enriched=False,
        )

        # Enrich with context if requested
        if show_context and hits and max_pages_with_context > 0:
            self._enrich_search_operation_with_context(search_result, max_pages_with_context, keyword)

        return search_result

    def _enrich_search_operation_with_context(
        self,
        search_result: SearchResult,
        page_limit: int,
        search_keyword: str,
    ) -> None:
        """Enrich search operation with contextual page content.

        Modifies the search operation in-place by fetching full page content
        for the specified hits.

        Args:
            search_result: The operation to enrich (modified in-place).
            page_limit: Maximum number of pages to enrich.
            search_keyword: Original search term for highlighting.
        """
        # Limit hits
        limited_hits = search_result.hits[:page_limit]

        search_result.hits = self.enrichment_service.enrich_hits_with_context(limited_hits, len(limited_hits), search_keyword)
        search_result.enriched = True

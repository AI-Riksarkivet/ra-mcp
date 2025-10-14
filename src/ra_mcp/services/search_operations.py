"""
Search operations that can be used by both CLI and MCP interfaces.
Handles keyword searching.
"""

from typing import Optional

from ..clients import SearchAPI
from ..models import SearchResult
from ..utils.http_client import HTTPClient


class SearchOperations:
    """Search operations for Riksarkivet document collections.

    Provides keyword search functionality.

    Attributes:
        search_api: Client for executing text searches.
    """

    def __init__(self, http_client: HTTPClient):
        self.search_api = SearchAPI(http_client=http_client)

    def search_transcribed(
        self,
        keyword: str,
        offset: int = 0,
        max_results: int = 10,
        max_hits_per_document: Optional[int] = None,
    ) -> SearchResult:
        """Search for transcribed text across document collections.

        Executes a keyword search across all transcribed documents in the Riksarkivet
        collections.

        Args:
            keyword: Search term or phrase to look for in transcribed text.
            offset: Number of results to skip for pagination.
            max_results: Maximum number of documents to return.
            max_hits_per_document: Limit hits per document (None for unlimited).

        Returns:
            SearchResult containing search hits, total count, and metadata.
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

        return search_result

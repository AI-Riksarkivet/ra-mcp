"""
Search operations that can be used by both CLI and MCP interfaces.
Handles keyword searching.
"""

from typing import Optional

from ra_mcp_core.utils.http_client import HTTPClient
from ra_mcp_core.models import SearchResult

from ..clients import SearchAPI


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
        max_snippets_per_record: Optional[int] = None,
    ) -> SearchResult:
        """Search for transcribed text across document collections.

        Executes a keyword search across all transcribed documents in the Riksarkivet
        collections.

        Args:
            keyword: Search term or phrase to look for in transcribed text.
            offset: Number of results to skip for pagination.
            max_results: Maximum number of documents to return.
            max_snippets_per_record: Limit snippets per document (None for unlimited).

        Returns:
            SearchResult containing documents, total count, and metadata.
        """
        # Execute search using API parameter names
        response = self.search_api.search_transcribed_text(
            transcribed_text=keyword,
            max=max_results,
            offset=offset,
            max_snippets_per_record=max_snippets_per_record
        )

        return SearchResult(
            response=response,
            transcribed_text=keyword,
            max=max_results,
            offset=offset,
            max_snippets_per_record=max_snippets_per_record
        )

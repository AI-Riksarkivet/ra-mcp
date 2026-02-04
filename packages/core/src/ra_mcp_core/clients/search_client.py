"""
Search API client for Riksarkivet.
"""

import logging
from typing import Dict, List, Optional, Union

from ..config import (
    SEARCH_API_BASE_URL,
    REQUEST_TIMEOUT,
    DEFAULT_MAX_RESULTS,
)
from ..models import SearchRecord
from ..utils.http_client import HTTPClient


logger = logging.getLogger(__name__)


class SearchAPI:
    """Client for Riksarkivet Search API."""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client
        self.logger = logging.getLogger("ra_mcp.search_api")
        self.logger.setLevel(logging.INFO)

    def search_transcribed_text(
        self,
        search_keyword: str,
        maximum_documents: int = DEFAULT_MAX_RESULTS,
        pagination_offset: int = 0,
        maximum_snippets_per_document: Optional[int] = None,
    ) -> tuple[List[SearchRecord], int]:
        """
        Search for keyword in transcribed materials.

        Args:
            search_keyword: Search term or Solr query
            maximum_documents: Maximum number of documents to fetch from API
            pagination_offset: Pagination offset for results
            maximum_snippets_per_document: Maximum number of snippets to keep per document (None = all)

        Returns:
            tuple: (list of SearchRecord objects, total number of results available)
        """
        self.logger.info(
            f"Starting search: keyword='{search_keyword}', max_docs={maximum_documents}, offset={pagination_offset}"
        )

        search_parameters = self._build_search_parameters(search_keyword, maximum_documents, pagination_offset)
        self.logger.debug(f"Search parameters: {search_parameters}")

        try:
            self.logger.info(f"Executing search request to {SEARCH_API_BASE_URL}...")
            search_result_data = self._execute_search_request(search_parameters)
            self.logger.info("Search request completed successfully")

            total_available_results = search_result_data.get("totalHits", 0)

            self.logger.debug("Parsing documents from API response...")
            documents = self._parse_documents(
                search_result_data.get("items", []),
                maximum_snippets_per_document
            )
            self.logger.info(f"Retrieved {len(documents)} documents")

            total_snippets = sum(doc.get_snippet_count() for doc in documents)
            self.logger.info(f"✓ Search completed: {total_snippets} snippet hits from {total_available_results} total documents")

            return documents, total_available_results

        except Exception as error:
            self.logger.error(f"✗ Search failed for keyword '{search_keyword}': {type(error).__name__}: {error}")
            raise Exception(f"Search failed: {error}") from error

    def _build_search_parameters(self, keyword: str, result_limit: int, offset: int) -> Dict[str, Union[str, int]]:
        """Build search API parameters."""
        return {
            "transcribed_text": keyword,
            "only_digitised_materials": "true",
            "max": result_limit,
            "offset": offset,
            "sort": "relevance",
        }

    def _execute_search_request(self, parameters: Dict) -> Dict:
        """Execute the search API request using centralized HTTP client."""
        return self.http_client.get_json(SEARCH_API_BASE_URL, params=parameters, timeout=REQUEST_TIMEOUT)

    def _parse_documents(
        self,
        items: List[Dict],
        max_snippets_per_doc: Optional[int] = None
    ) -> List[SearchRecord]:
        """
        Parse API response items into SearchRecord objects.

        Args:
            items: List of document items from API response
            max_snippets_per_doc: Maximum snippets to keep per document (None = all)

        Returns:
            List of SearchRecord objects
        """
        documents = []

        for item in items:
            try:
                # Parse document using Pydantic
                document = SearchRecord(**item)

                # Limit snippets if requested
                if max_snippets_per_doc and document.transcribed_text:
                    document.transcribed_text.snippets = document.transcribed_text.snippets[:max_snippets_per_doc]

                documents.append(document)

            except Exception as e:
                self.logger.warning(f"Failed to parse document {item.get('id', 'unknown')}: {e}")
                continue

        return documents

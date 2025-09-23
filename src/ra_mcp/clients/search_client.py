"""
Search API client for Riksarkivet.
"""

import re
from typing import Dict, List, Optional, Tuple, Union

from ..config import SEARCH_API_BASE_URL, REQUEST_TIMEOUT, DEFAULT_MAX_RESULTS
from ..models import SearchHit
from ..utils import HTTPClient, URLGenerator


class SearchAPI:
    """Client for Riksarkivet Search API."""

    def __init__(self):
        self.session = HTTPClient.create_session()

    def search_transcribed_text(
        self,
        search_keyword: str,
        maximum_documents: int = DEFAULT_MAX_RESULTS,
        pagination_offset: int = 0,
        maximum_hits_per_document: Optional[int] = None,
    ) -> Tuple[List[SearchHit], int]:
        """Fast search for keyword in transcribed materials.

        Args:
            keyword: Search term
            max_results: Maximum number of documents to fetch from API
            offset: Pagination offset
            max_hits_per_document: Maximum number of page hits to return per document (None = all)

        Returns:
            tuple: (list of SearchHit objects, total number of results)
        """
        search_parameters = {
            "transcribed_text": search_keyword,
            "only_digitised_materials": "true",
            "max": maximum_documents,
            "offset": pagination_offset,
            "sort": "relevance",
        }

        try:
            api_response = self.session.get(
                SEARCH_API_BASE_URL, params=search_parameters, timeout=REQUEST_TIMEOUT
            )
            api_response.raise_for_status()
            response_data = api_response.json()

            document_items = response_data.get("items", [])

            if maximum_documents and len(document_items) > maximum_documents:
                document_items = document_items[:maximum_documents]

            search_hits = []
            for document_item in document_items:
                document_hits = self._process_search_item(document_item, maximum_hits_per_document)
                search_hits.extend(document_hits)

            total_available_hits = response_data.get("totalHits", len(search_hits))

            return search_hits, total_available_hits

        except Exception as error:
            raise Exception(f"Search failed: {error}") from error

    def _process_search_item(
        self, document_item: Dict[str, Union[str, Dict, List]], maximum_hits: Optional[int] = None
    ) -> List[SearchHit]:
        """Process a single search result item into SearchHit objects."""
        document_metadata = document_item.get("metadata", {})
        transcribed_text_data = document_item.get("transcribedText", {})

        document_pid = document_item.get("id", "Unknown")
        document_title = document_item.get("caption", "(No title)")
        document_reference_code = document_metadata.get("referenceCode", "")

        document_hierarchy = document_metadata.get("hierarchy", [])
        document_note = document_metadata.get("note")
        document_institution = document_metadata.get("archivalInstitution", [])
        document_date = document_metadata.get("date")

        document_collection_url = URLGenerator.collection_url(document_pid) if document_pid else None
        document_manifest_url = URLGenerator.manifest_url(document_pid) if document_pid else None

        document_hits = []
        if transcribed_text_data and "snippets" in transcribed_text_data:
            for text_snippet in transcribed_text_data["snippets"]:
                snippet_pages = text_snippet.get("pages", [])
                for page_info in snippet_pages:
                    if maximum_hits is not None and len(document_hits) >= maximum_hits:
                        return document_hits

                    page_identifier = (
                        page_info.get("id", "").lstrip("_")
                        if isinstance(page_info, dict)
                        else str(page_info)
                    )

                    search_hit = SearchHit(
                        pid=document_pid,
                        title=document_title[:100] + "..." if len(document_title) > 100 else document_title,
                        reference_code=document_reference_code,
                        page_number=page_identifier,
                        snippet_text=self._clean_html(text_snippet.get("text", "")),
                        score=text_snippet.get("score", 0),
                        hierarchy=document_hierarchy,
                        note=document_note,
                        collection_url=document_collection_url,
                        manifest_url=document_manifest_url,
                        archival_institution=document_institution,
                        date=document_date,
                    )
                    document_hits.append(search_hit)
        return document_hits

    def _clean_html(html_text: str) -> str:
        """Remove HTML tags from text."""
        return re.sub(r"<[^>]+>", "", html_text)

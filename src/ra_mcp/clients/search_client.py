"""
Search API client for Riksarkivet.
"""

import re
from typing import Dict, List, Optional, Tuple, Union

from ..config import SEARCH_API_BASE_URL, REQUEST_TIMEOUT, DEFAULT_MAX_RESULTS
from ..models import SearchHit
from ..utils import create_session, url_generator


class SearchAPI:
    """Client for Riksarkivet Search API."""

    def __init__(self):
        self.session = create_session()

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
        search_parameters = self._build_search_parameters(
            search_keyword, maximum_documents, pagination_offset
        )

        try:
            api_response = self._execute_search_request(search_parameters)
            search_result_data = api_response.json()

            retrieved_documents = self._extract_documents_from_response(
                search_result_data, maximum_documents
            )

            collected_search_hits = self._collect_hits_from_documents(
                retrieved_documents, maximum_hits_per_document
            )

            total_available_results = search_result_data.get(
                "totalHits", len(collected_search_hits)
            )

            return collected_search_hits, total_available_results

        except Exception as error:
            raise Exception(f"Search failed: {error}") from error

    def _build_search_parameters(
        self, keyword: str, result_limit: int, offset: int
    ) -> Dict[str, Union[str, int]]:
        """Build search API parameters."""
        return {
            "transcribed_text": keyword,
            "only_digitised_materials": "true",
            "max": result_limit,
            "offset": offset,
            "sort": "relevance",
        }

    def _execute_search_request(self, parameters: Dict) -> object:
        """Execute the search API request."""
        response = self.session.get(
            SEARCH_API_BASE_URL, params=parameters, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response

    def _extract_documents_from_response(
        self, response_data: Dict, document_limit: Optional[int]
    ) -> List[Dict]:
        """Extract and limit documents from API response."""
        available_documents = response_data.get("items", [])

        if document_limit and len(available_documents) > document_limit:
            return available_documents[:document_limit]

        return available_documents

    def _collect_hits_from_documents(
        self, documents: List[Dict], hits_per_document_limit: Optional[int]
    ) -> List[SearchHit]:
        """Collect all search hits from documents."""
        all_hits = []
        for document in documents:
            document_hits = self._process_search_item(document, hits_per_document_limit)
            all_hits.extend(document_hits)
        return all_hits

    def _process_search_item(
        self,
        document_item: Dict[str, Union[str, Dict, List]],
        maximum_hits: Optional[int] = None,
    ) -> List[SearchHit]:
        """Process a single search result item into SearchHit objects."""
        document_info = self._extract_document_information(document_item)
        transcribed_content = document_item.get("transcribedText", {})

        if not transcribed_content or "snippets" not in transcribed_content:
            return []

        return self._process_document_snippets(
            transcribed_content["snippets"], document_info, maximum_hits
        )

    def _extract_document_information(self, document: Dict) -> Dict:
        """Extract all document information and metadata."""
        metadata = document.get("metadata", {})
        persistent_identifier = document.get("id", "Unknown")

        return {
            "pid": persistent_identifier,
            "title": self._truncate_title(document.get("caption", "(No title)")),
            "reference_code": metadata.get("referenceCode", ""),
            "hierarchy": metadata.get("hierarchy", []),
            "note": metadata.get("note"),
            "archival_institution": metadata.get("archivalInstitution", []),
            "date": metadata.get("date"),
            "collection_url": url_generator.collection_url(persistent_identifier)
            if persistent_identifier
            else None,
            "manifest_url": url_generator.manifest_url(persistent_identifier)
            if persistent_identifier
            else None,
        }

    def _truncate_title(self, title: str, max_length: int = 100) -> str:
        """Truncate title if it exceeds maximum length."""
        if len(title) > max_length:
            return f"{title[:max_length]}..."
        return title

    def _process_document_snippets(
        self, snippets: List[Dict], document_info: Dict, hit_limit: Optional[int]
    ) -> List[SearchHit]:
        """Process all snippets from a document into search hits."""
        processed_hits = []

        for snippet in snippets:
            snippet_hits = self._process_single_snippet(
                snippet, document_info, hit_limit, len(processed_hits)
            )
            processed_hits.extend(snippet_hits)

            if hit_limit and len(processed_hits) >= hit_limit:
                return processed_hits[:hit_limit]

        return processed_hits

    def _process_single_snippet(
        self,
        snippet: Dict,
        document_info: Dict,
        hit_limit: Optional[int],
        current_hit_count: int,
    ) -> List[SearchHit]:
        """Process a single snippet into search hits."""
        snippet_pages = snippet.get("pages", [])
        snippet_hits = []

        for page_data in snippet_pages:
            if hit_limit and current_hit_count + len(snippet_hits) >= hit_limit:
                break

            page_number = self._extract_page_number(page_data)
            cleaned_text = self._clean_html(snippet.get("text", ""))

            hit = self._create_search_hit(
                document_info, page_number, cleaned_text, snippet.get("score", 0)
            )
            snippet_hits.append(hit)

        return snippet_hits

    def _extract_page_number(self, page_data: Union[Dict, str]) -> str:
        """Extract and normalize page number from page data."""
        if isinstance(page_data, dict):
            return page_data.get("id", "").lstrip("_")
        return str(page_data)

    def _create_search_hit(
        self,
        document_info: Dict,
        page_number: str,
        snippet_text: str,
        relevance_score: float,
    ) -> SearchHit:
        """Create a SearchHit object from document and snippet information."""
        return SearchHit(
            pid=document_info["pid"],
            title=document_info["title"],
            reference_code=document_info["reference_code"],
            page_number=page_number,
            snippet_text=snippet_text,
            score=relevance_score,
            hierarchy=document_info["hierarchy"],
            note=document_info["note"],
            collection_url=document_info["collection_url"],
            manifest_url=document_info["manifest_url"],
            archival_institution=document_info["archival_institution"],
            date=document_info["date"],
        )

    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags from text."""
        return re.sub(r"<[^>]+>", "", html_text)

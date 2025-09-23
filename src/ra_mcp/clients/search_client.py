"""
Search API client for Riksarkivet.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from ..config import SEARCH_API_BASE_URL, REQUEST_TIMEOUT, DEFAULT_MAX_RESULTS
from ..models import SearchHit
from ..utils import HTTPClient, URLGenerator


class SearchAPI:
    """Client for Riksarkivet Search API."""

    def __init__(self):
        self.session = HTTPClient.create_session()

    def search_transcribed_text(
        self,
        keyword: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        offset: int = 0,
        max_hits_per_document: Optional[int] = None
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
        params = {
            'transcribed_text': keyword,
            'only_digitised_materials': 'true',
            'max': max_results,
            'offset': offset,
            'sort': 'relevance'
        }

        try:
            response = self.session.get(SEARCH_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Get items from response
            items = data.get('items', [])

            # IMPORTANT: The API doesn't respect the 'max' parameter properly,
            # so we need to limit the documents ourselves
            if max_results and len(items) > max_results:
                items = items[:max_results]

            hits = []
            for item in items:
                # Pass max_hits_per_document directly to _process_search_item
                item_hits = self._process_search_item(item, max_hits_per_document)
                hits.extend(item_hits)

            # Get total hits from response - this is the total available in the API
            total_hits = data.get('totalHits', len(hits))

            # Return hits with metadata about total results
            return hits, total_hits

        except Exception as e:
            # Raise exception instead of printing
            raise Exception(f"Search failed: {e}") from e

    def _process_search_item(self, item: Dict[str, Any], max_hits: Optional[int] = None) -> List[SearchHit]:
        """Process a single search result item into SearchHit objects."""
        metadata = item.get('metadata', {})
        transcribed_data = item.get('transcribedText', {})

        # Extract basic info
        pid = item.get('id', 'Unknown')
        title = item.get('caption', '(No title)')
        reference_code = metadata.get('referenceCode', '')

        # Extract enhanced metadata
        hierarchy = metadata.get('hierarchy', [])
        note = metadata.get('note')
        archival_institution = metadata.get('archivalInstitution', [])
        date = metadata.get('date')

        # Generate URLs
        collection_url = URLGenerator.collection_url(pid) if pid else None
        manifest_url = URLGenerator.manifest_url(pid) if pid else None

        hits = []
        if transcribed_data and 'snippets' in transcribed_data:
            for snippet in transcribed_data['snippets']:
                pages = snippet.get('pages', [])
                for page in pages:
                    # Check if we've reached the max hits limit for this document
                    if max_hits is not None and len(hits) >= max_hits:
                        return hits

                    page_id = page.get('id', '').lstrip('_') if isinstance(page, dict) else str(page)

                    hit = SearchHit(
                        pid=pid,
                        title=title[:100] + '...' if len(title) > 100 else title,
                        reference_code=reference_code,
                        page_number=page_id,
                        snippet_text=self._clean_html(snippet.get('text', '')),
                        score=snippet.get('score', 0),
                        hierarchy=hierarchy,
                        note=note,
                        collection_url=collection_url,
                        manifest_url=manifest_url,
                        archival_institution=archival_institution,
                        date=date
                    )
                    hits.append(hit)
        return hits

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove HTML tags from text."""
        return re.sub(r'<[^>]+>', '', text)
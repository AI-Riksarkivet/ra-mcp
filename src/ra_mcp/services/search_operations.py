"""
Unified search operations that can be used by both CLI and MCP interfaces.
This eliminates code duplication between CLI commands and MCP tools.
"""

from typing import List, Optional, Tuple, Dict, Union

from ..clients import SearchAPI, IIIFClient, OAIPMHClient
from ..models import SearchHit, SearchOperation, BrowseOperation
from ..utils import HTTPClient, parse_page_range
from ..config import SEARCH_API_BASE_URL, REQUEST_TIMEOUT
from .search_enrichment_service import SearchEnrichmentService
from .page_context_service import PageContextService


class SearchOperations:
    """
    Unified search operations that can be used by both CLI and MCP interfaces.
    Contains all the business logic for search, browse, and context operations.
    """

    def __init__(self):
        self.search_api = SearchAPI()
        self.enrichment_service = SearchEnrichmentService()
        self.page_service = PageContextService()
        self.iiif_client = IIIFClient()
        self.oai_client = OAIPMHClient()

    def search_transcribed(
        self,
        keyword: str,
        offset: int = 0,
        max_results: int = 10,
        max_hits_per_document: Optional[int] = None,
        show_context: bool = False,
        max_pages_with_context: int = 0,
        context_padding: int = 0,
    ) -> SearchOperation:
        """
        Unified search operation that can be used by both CLI and MCP.

        Returns SearchOperation with results and metadata.
        """
        hits, total_hits = self.search_api.search_transcribed_text(
            keyword, max_results, offset, max_hits_per_document
        )

        operation = SearchOperation(
            hits=hits,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            enriched=False,
        )

        if show_context and hits and max_pages_with_context > 0:
            hits_to_enrich = hits[:max_pages_with_context]

            if context_padding > 0:
                hits_to_enrich = (
                    self.enrichment_service.expand_hits_with_context_padding(
                        hits_to_enrich, context_padding
                    )
                )

            enriched_hits = self.enrichment_service.enrich_hits_with_context(
                hits_to_enrich, len(hits_to_enrich), keyword
            )

            operation.hits = enriched_hits
            operation.enriched = True

        return operation

    def browse_document(
        self,
        reference_code: str,
        pages: str,
        highlight_term: Optional[str] = None,
        max_pages: int = 20,
    ) -> BrowseOperation:
        """
        Unified browse operation that can be used by both CLI and MCP.

        Returns BrowseOperation with page contexts and metadata.
        """
        pid = self._find_pid_for_reference(reference_code)

        if not pid:
            return BrowseOperation(
                contexts=[],
                reference_code=reference_code,
                pages_requested=pages,
                pid=None,
            )

        collection_info = self.iiif_client.explore_collection(pid)
        manifest_id = pid
        if collection_info and collection_info.get("manifests"):
            manifest_id = collection_info["manifests"][0]["id"]

        selected_pages = parse_page_range(pages)[:max_pages]

        contexts = []
        for page_num in selected_pages:
            context = self.page_service.get_page_context(
                manifest_id, str(page_num), reference_code, highlight_term
            )
            if context:
                contexts.append(context)

        return BrowseOperation(
            contexts=contexts,
            reference_code=reference_code,
            pages_requested=pages,
            pid=pid,
            manifest_id=manifest_id,
        )

    def show_pages_with_context(
        self,
        keyword: str,
        max_pages: int = 10,
        context_padding: int = 1,
        search_limit: int = 50,
    ) -> Tuple[SearchOperation, List[SearchHit]]:
        """
        Unified show-pages operation that combines search and context display.

        Returns:
        - SearchOperation with the initial search results
        - List of enriched hits with context padding and full text
        """
        search_op = self.search_transcribed(
            keyword=keyword, max_results=search_limit, show_context=False
        )

        if not search_op.hits:
            return search_op, []

        display_hits = search_op.hits[:max_pages]

        expanded_hits = self.enrichment_service.expand_hits_with_context_padding(
            display_hits, context_padding
        )

        enriched_hits = self.enrichment_service.enrich_hits_with_context(
            expanded_hits, len(expanded_hits), keyword
        )

        return search_op, enriched_hits

    def get_document_structure(
        self, reference_code: Optional[str] = None, pid: Optional[str] = None
    ) -> Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Get document structure information.

        Returns IIIF collection info or None if not found.
        """
        if not reference_code and not pid:
            return None

        # Get PID if only reference_code provided
        if reference_code and not pid:
            pid = self._find_pid_for_reference(reference_code)

        if not pid:
            return None

        # Clean PID if needed
        clean_pid = pid[6:] if pid.startswith("arkis!") else pid

        # Get IIIF collection info
        collection_info = self.iiif_client.explore_collection(clean_pid)
        return collection_info

    def _find_pid_for_reference(self, reference_code: str) -> Optional[str]:
        """
        Find PID for a reference code using multiple strategies.

        Returns PID or None if not found.
        """
        session = HTTPClient.create_session()
        pid = None

        # Try search API first
        try:
            params = {
                "reference_code": reference_code,
                "only_digitised_materials": "true",
                "max": 1,
            }
            response = session.get(
                SEARCH_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            if data.get("items"):
                pid = data["items"][0].get("id")
        except Exception:
            pass

        # Fall back to OAI-PMH if search failed
        if not pid:
            try:
                pid = self.oai_client.extract_pid(reference_code)
            except Exception:
                pass

        return pid


class SearchResultsAnalyzer:
    """
    Utility class for analyzing search results and generating insights.
    Used by both CLI and MCP for result analysis.
    """

    @staticmethod
    def group_hits_by_document(hits: List[SearchHit]) -> Dict[str, List[SearchHit]]:
        """Group search hits by document (reference code or PID)."""
        grouped = {}
        for hit in hits:
            key = hit.reference_code or hit.pid
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(hit)
        return grouped

    @staticmethod
    def get_pagination_info(
        hits: List[SearchHit], total_hits: int, offset: int, max_results: int
    ) -> Dict[str, Union[int, bool, Optional[int]]]:
        """Calculate pagination information for search results."""
        # Count unique documents
        unique_docs = set()
        for hit in hits:
            unique_docs.add(hit.reference_code or hit.pid)

        has_more = len(unique_docs) == max_results and total_hits > len(hits)
        document_start = offset // max_results * max_results + 1
        document_end = document_start + len(unique_docs) - 1

        return {
            "total_hits": total_hits,
            "total_documents_shown": len(unique_docs),
            "total_page_hits": len(hits),
            "document_range_start": document_start,
            "document_range_end": document_end,
            "has_more": has_more,
            "next_offset": offset + max_results if has_more else None,
        }

    @staticmethod
    def extract_search_summary(
        operation: SearchOperation,
    ) -> Dict[str, Union[str, int, bool, Dict[str, List[SearchHit]]]]:
        """Extract summary information from a search operation."""
        grouped = SearchResultsAnalyzer.group_hits_by_document(operation.hits)

        return {
            "keyword": operation.keyword,
            "total_hits": operation.total_hits,
            "page_hits_returned": len(operation.hits),
            "documents_returned": len(grouped),
            "enriched": operation.enriched,
            "offset": operation.offset,
            "grouped_hits": grouped,
        }

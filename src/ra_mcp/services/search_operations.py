"""
Unified search operations that can be used by both CLI and MCP interfaces.
This eliminates code duplication between CLI commands and MCP tools.
"""

from typing import List, Optional, Tuple, Dict, Union

from ..clients import SearchAPI, IIIFClient, OAIPMHClient
from ..models import SearchHit, SearchOperation, BrowseOperation
from ..utils import parse_page_range
from ..utils.http_client import HTTPClient
from ..config import SEARCH_API_BASE_URL, REQUEST_TIMEOUT
from .search_enrichment_service import SearchEnrichmentService
from .page_context_service import PageContextService


class SearchOperations:
    """
    Unified search operations that can be used by both CLI and MCP interfaces.
    Contains all the business logic for search, browse, and context operations.
    """

    def __init__(self):
        self.http = HTTPClient()
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
        search_results = self._execute_transcribed_search(
            keyword, max_results, offset, max_hits_per_document
        )

        search_operation = self._build_search_operation(search_results, keyword, offset)

        if self._should_enrich_with_context(
            show_context, search_results[0], max_pages_with_context
        ):
            self._enrich_search_operation_with_context(
                search_operation, max_pages_with_context, context_padding, keyword
            )

        return search_operation

    def _execute_transcribed_search(
        self,
        search_keyword: str,
        result_limit: int,
        pagination_offset: int,
        hits_per_document_limit: Optional[int],
    ) -> Tuple[List[SearchHit], int]:
        """Execute the transcribed text search."""
        return self.search_api.search_transcribed_text(
            search_keyword, result_limit, pagination_offset, hits_per_document_limit
        )

    def _build_search_operation(
        self,
        search_results: Tuple[List[SearchHit], int],
        search_keyword: str,
        pagination_offset: int,
    ) -> SearchOperation:
        """Build SearchOperation from search results."""
        retrieved_hits, total_hit_count = search_results

        return SearchOperation(
            hits=retrieved_hits,
            total_hits=total_hit_count,
            keyword=search_keyword,
            offset=pagination_offset,
            enriched=False,
        )

    def _should_enrich_with_context(
        self,
        context_requested: bool,
        search_hits: List[SearchHit],
        context_page_limit: int,
    ) -> bool:
        """Check if search results should be enriched with context."""
        return context_requested and search_hits and context_page_limit > 0

    def _enrich_search_operation_with_context(
        self,
        search_operation: SearchOperation,
        page_limit: int,
        padding_size: int,
        search_keyword: str,
    ) -> None:
        """Enrich search operation with context information."""
        hits_for_enrichment = self._prepare_hits_for_enrichment(
            search_operation.hits, page_limit, padding_size
        )

        enriched_hit_collection = self.enrichment_service.enrich_hits_with_context(
            hits_for_enrichment, len(hits_for_enrichment), search_keyword
        )

        search_operation.hits = enriched_hit_collection
        search_operation.enriched = True

    def _prepare_hits_for_enrichment(
        self, original_hits: List[SearchHit], page_limit: int, padding_size: int
    ) -> List[SearchHit]:
        """Prepare hits for enrichment by limiting and expanding with padding."""
        limited_hits = original_hits[:page_limit]

        if padding_size > 0:
            return self.enrichment_service.expand_hits_with_context_padding(
                limited_hits, padding_size
            )

        return limited_hits

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
        persistent_identifier = self._find_pid_for_reference(reference_code)

        if not persistent_identifier:
            return self._create_empty_browse_operation(reference_code, pages)

        manifest_identifier = self._resolve_manifest_identifier(persistent_identifier)

        page_contexts = self._fetch_page_contexts(
            manifest_identifier, pages, max_pages, reference_code, highlight_term
        )

        return self._create_browse_operation(
            page_contexts,
            reference_code,
            pages,
            persistent_identifier,
            manifest_identifier,
        )

    def _create_empty_browse_operation(
        self, reference_code: str, requested_pages: str
    ) -> BrowseOperation:
        """Create an empty BrowseOperation when no PID is found."""
        return BrowseOperation(
            contexts=[],
            reference_code=reference_code,
            pages_requested=requested_pages,
            pid=None,
        )

    def _resolve_manifest_identifier(self, persistent_identifier: str) -> str:
        """Resolve manifest identifier from PID."""
        iiif_collection_info = self.iiif_client.explore_collection(
            persistent_identifier
        )

        if self._has_manifests(iiif_collection_info):
            manifest_id = iiif_collection_info["manifests"][0]["id"]
            return manifest_id

        return persistent_identifier

    def _has_manifests(self, collection_info: Optional[Dict]) -> bool:
        """Check if collection info contains manifests."""
        return bool(collection_info and collection_info.get("manifests"))

    def _fetch_page_contexts(
        self,
        manifest_identifier: str,
        page_specification: str,
        maximum_pages: int,
        reference_code: str,
        highlight_keyword: Optional[str],
    ) -> List:
        """Fetch contexts for specified pages."""
        requested_page_numbers = self._parse_and_limit_pages(
            page_specification, maximum_pages
        )

        page_context_collection = []

        for page_number in requested_page_numbers:
            page_context = self._fetch_single_page_context(
                manifest_identifier, page_number, reference_code, highlight_keyword
            )
            if page_context:
                page_context_collection.append(page_context)

        return page_context_collection

    def _parse_and_limit_pages(self, page_specification: str, limit: int) -> List[int]:
        """Parse page specification and apply limit."""
        parsed_pages = parse_page_range(page_specification)
        return parsed_pages[:limit]

    def _fetch_single_page_context(
        self,
        manifest_identifier: str,
        page_number: int,
        reference_code: str,
        highlight_keyword: Optional[str],
    ):
        """Fetch context for a single page."""
        return self.page_service.get_page_context(
            manifest_identifier, str(page_number), reference_code, highlight_keyword
        )

    def _create_browse_operation(
        self,
        contexts: List,
        reference_code: str,
        requested_pages: str,
        persistent_identifier: str,
        manifest_identifier: str,
    ) -> BrowseOperation:
        """Create BrowseOperation with all data."""
        return BrowseOperation(
            contexts=contexts,
            reference_code=reference_code,
            pages_requested=requested_pages,
            pid=persistent_identifier,
            manifest_id=manifest_identifier,
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
        resolved_pid = self._resolve_document_pid(reference_code, pid)

        if not resolved_pid:
            return None

        cleaned_pid = self._clean_pid_identifier(resolved_pid)
        iiif_collection_structure = self.iiif_client.explore_collection(cleaned_pid)

        return iiif_collection_structure

    def _resolve_document_pid(
        self, reference_code: Optional[str], provided_pid: Optional[str]
    ) -> Optional[str]:
        """Resolve PID from reference code or use provided PID."""
        if not reference_code and not provided_pid:
            return None

        if provided_pid:
            return provided_pid

        return self._find_pid_for_reference(reference_code)

    def _clean_pid_identifier(self, pid: str) -> str:
        """Clean PID identifier by removing arkis! prefix if present."""
        arkis_prefix = "arkis!"

        if pid.startswith(arkis_prefix):
            return pid[len(arkis_prefix) :]

        return pid

    def _find_pid_for_reference(self, reference_code: str) -> Optional[str]:
        """
        Find PID for a reference code using multiple strategies.

        Returns PID or None if not found.
        """
        persistent_identifier = self._search_pid_via_api(reference_code)

        if not persistent_identifier:
            persistent_identifier = self._search_pid_via_oai_pmh(reference_code)

        return persistent_identifier

    def _search_pid_via_api(self, reference_code: str) -> Optional[str]:
        """Search for PID using the search API."""
        try:
            search_parameters = self._build_pid_search_parameters(reference_code)
            api_response = self._execute_pid_search_request(search_parameters)

            return self._extract_pid_from_search_response(api_response)
        except Exception:
            return None

    def _build_pid_search_parameters(
        self, reference_code: str
    ) -> Dict[str, Union[str, int]]:
        """Build parameters for PID search."""
        return {
            "reference_code": reference_code,
            "only_digitised_materials": "true",
            "max": 1,
        }

    def _execute_pid_search_request(self, parameters: Dict) -> Dict:
        """Execute search request for PID using centralized HTTP client."""
        return self.http.get_json(
            SEARCH_API_BASE_URL, params=parameters, timeout=REQUEST_TIMEOUT
        )

    def _extract_pid_from_search_response(self, response_data: Dict) -> Optional[str]:
        """Extract PID from search API response."""
        search_items = response_data.get("items", [])

        if search_items:
            return search_items[0].get("id")

        return None

    def _search_pid_via_oai_pmh(self, reference_code: str) -> Optional[str]:
        """Search for PID using OAI-PMH client."""
        try:
            return self.oai_client.extract_pid(reference_code)
        except Exception:
            return None

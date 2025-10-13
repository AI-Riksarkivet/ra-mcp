"""
Unified search operations that can be used by both CLI and MCP interfaces.
This eliminates code duplication between CLI commands and MCP tools.
"""

from typing import List, Optional

from ..clients import SearchAPI, IIIFClient
from ..models import SearchOperation, BrowseOperation, DocumentMetadata
from ..utils import parse_page_range
from .search_enrichment_service import SearchEnrichmentService
from .page_context_service import PageContextService
from ..utils.http_client import HTTPClient


class SearchOperations:
    """Search operations for Riksarkivet document collections.

    Provides search, browse, and context operations for interacting with
    Riksarkivet's search APIs, IIIF services, and enrichment services.

    Attributes:
        search_api: Client for executing text searches.
        enrichment_service: Service for enriching search results with context.
        page_service: Service for fetching page-level context and content.
        iiif_client: Client for interacting with IIIF collections and manifests.
    """

    def __init__(self, http_client: HTTPClient):
        self.search_api = SearchAPI(http_client=http_client)
        self.enrichment_service = SearchEnrichmentService(http_client=http_client)
        self.page_service = PageContextService(http_client=http_client)
        self.iiif_client = IIIFClient(http_client=http_client)

    def search_transcribed(
        self,
        keyword: str,
        offset: int = 0,
        max_results: int = 10,
        max_hits_per_document: Optional[int] = None,
        show_context: bool = False,
        max_pages_with_context: int = 0,
    ) -> SearchOperation:
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
            SearchOperation containing search hits, total count, and metadata.
            If show_context is True, hits will include enriched page content.
        """
        # Execute search and build operation in one step
        hits, total_hits = self.search_api.search_transcribed_text(keyword, max_results, offset, max_hits_per_document)

        search_operation = SearchOperation(
            hits=hits,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            enriched=False,
        )

        # Enrich with context if requested
        if show_context and hits and max_pages_with_context > 0:
            self._enrich_search_operation_with_context(search_operation, max_pages_with_context, keyword)

        return search_operation

    def _enrich_search_operation_with_context(
        self,
        search_operation: SearchOperation,
        page_limit: int,
        search_keyword: str,
    ) -> None:
        """Enrich search operation with contextual page content.

        Modifies the search operation in-place by fetching full page content
        for the specified hits.

        Args:
            search_operation: The operation to enrich (modified in-place).
            page_limit: Maximum number of pages to enrich.
            search_keyword: Original search term for highlighting.
        """
        # Limit hits
        limited_hits = search_operation.hits[:page_limit]

        search_operation.hits = self.enrichment_service.enrich_hits_with_context(limited_hits, len(limited_hits), search_keyword)
        search_operation.enriched = True

    def browse_document(
        self,
        reference_code: str,
        pages: str,
        highlight_term: Optional[str] = None,
        max_pages: int = 20,
    ) -> BrowseOperation:
        """Browse specific pages of a document.

        Retrieves full transcribed content for specified pages of a document,
        with optional term highlighting. Supports various page specifications
        including ranges (1-5), lists (1,3,5), and combinations.

        Args:
            reference_code: Document identifier (e.g., 'SE/RA/730128/730128.006').
            pages: Page specification (e.g., '1-3,5,7-9' or 'all').
            highlight_term: Optional term to highlight in the returned text.
            max_pages: Maximum number of pages to retrieve.

        Returns:
            BrowseOperation containing page contexts, document metadata,
            and persistent identifiers. Returns empty contexts if document
            not found or no valid pages.
        """
        manifset_id = self.page_service.oai_client.extract_manifset_id(reference_code)

        if not manifset_id:
            return BrowseOperation(
                contexts=[],
                reference_code=reference_code,
                pages_requested=pages,
              
            )

        page_contexts = self._fetch_page_contexts(manifset_id, pages, max_pages, reference_code, highlight_term)

        # Fetch document metadata by searching for the reference code
        document_metadata = self._fetch_document_metadata(reference_code)
     

        return BrowseOperation(
            contexts=page_contexts,
            reference_code=reference_code,
            pages_requested=pages,
            manifest_id=manifset_id,
            document_metadata=document_metadata,
        )

    def _resolve_manifest_identifier(self, persistent_identifier: str) -> str:
        """Resolve IIIF manifest identifier from persistent identifier.

        Attempts to find the appropriate IIIF manifest for a given PID.
        If the PID points to a collection with manifests, returns the first
        manifest ID. Otherwise returns the original PID.

        Args:
            persistent_identifier: Document PID to resolve.

        Returns:
            IIIF manifest identifier or original PID if no manifest found.
        """
        iiif_collection_info = self.iiif_client.explore_collection(persistent_identifier)

        # Return first manifest ID if available, otherwise use PID
        if iiif_collection_info and iiif_collection_info.get("manifests"):
            return iiif_collection_info["manifests"][0]["id"]

        return persistent_identifier

    def _fetch_page_contexts(
        self,
        manifest_identifier: str,
        page_specification: str,
        maximum_pages: int,
        reference_code: str,
        highlight_keyword: Optional[str],
    ) -> List:
        """Fetch page contexts for specified page numbers.

        Retrieves full page content for each specified page number,
        with optional keyword highlighting.

        Args:
            manifest_identifier: IIIF manifest ID to fetch pages from.
            page_specification: Page range specification (e.g., '1-5,7').
            maximum_pages: Maximum pages to fetch.
            reference_code: Document reference for context.
            highlight_keyword: Optional term to highlight.

        Returns:
            List of page context objects with transcribed text and metadata.
        """
        # Parse and limit page numbers
        page_numbers = parse_page_range(page_specification)[:maximum_pages]

        # Fetch context for each page
        page_contexts = []
        for page_number in page_numbers:
            page_context = self.page_service.get_page_context(manifest_identifier, str(page_number), reference_code, highlight_keyword)
            if page_context:
                page_contexts.append(page_context)

        return page_contexts

    def _fetch_document_metadata(self, reference_code: str) -> Optional[DocumentMetadata]:
        """Fetch document metadata by searching for the reference code.

        Args:
            reference_code: Document reference code to get metadata for.

        Returns:
            Dictionary containing document metadata (hierarchy, institution, etc.)
            or None if not found.
        """
        try:
          


            return None
        except Exception:
            # If metadata fetch fails, return None - browse will still work
            return None

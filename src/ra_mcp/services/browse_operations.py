"""
Browse operations for viewing document pages.
Handles document browsing, page fetching, and metadata retrieval.
"""

from typing import List, Optional

from ..clients import IIIFClient, ALTOClient, OAIPMHClient
from ..models import BrowseResult, DocumentMetadata, PageContext
from ..utils import parse_page_range, url_generator
from ..utils.http_client import HTTPClient


class BrowseOperations:
    """Browse operations for Riksarkivet document collections.

    Provides document browsing functionality for viewing specific pages
    of documents by reference code.

    Attributes:
        alto_client: Client for fetching ALTO XML content.
        oai_client: Client for OAI-PMH metadata operations.
        iiif_client: Client for interacting with IIIF collections and manifests.
    """

    def __init__(self, http_client: HTTPClient):
        self.alto_client = ALTOClient(http_client=http_client)
        self.oai_client = OAIPMHClient(http_client=http_client)
        self.iiif_client = IIIFClient(http_client=http_client)

    def browse_document(
        self,
        reference_code: str,
        pages: str,
        highlight_term: Optional[str] = None,
        max_pages: int = 20,
    ) -> BrowseResult:
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
            BrowseResult containing page contexts, document metadata,
            and persistent identifiers. Returns empty contexts if document
            not found or no valid pages.
        """
        manifset_id = self.oai_client.extract_manifset_id(reference_code)

        if not manifset_id:
            return BrowseResult(
                contexts=[],
                reference_code=reference_code,
                pages_requested=pages,
            )

        page_contexts = self._fetch_page_contexts(manifset_id, pages, max_pages, reference_code, highlight_term)

        # Fetch document metadata by searching for the reference code
        document_metadata = self._fetch_document_metadata(reference_code)

        return BrowseResult(
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
            page_context = self._get_page_context(
                manifest_identifier, str(page_number), reference_code, highlight_keyword
            )
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

    def _get_page_context(
        self,
        manifest_id: str,
        page_number: str,
        reference_code: str = "",
        search_term: Optional[str] = None,
    ) -> Optional[PageContext]:
        """Get full page context for a specific page using manifest ID for ALTO URL generation.

        Args:
            manifest_id: IIIF manifest identifier.
            page_number: Page number to fetch.
            reference_code: Document reference code.
            search_term: Optional search term for bildvisning URL.

        Returns:
            PageContext object with transcribed text and metadata, or None if not found.
        """
        cleaned_manifest_id = url_generator.remove_arkis_prefix(manifest_id)
        alto_xml_url = url_generator.alto_url(cleaned_manifest_id, page_number)
        image_url_link = url_generator.iiif_image_url(manifest_id, page_number)
        bildvisning_link = url_generator.bildvisning_url(manifest_id, page_number, search_term)

        if not alto_xml_url:
            return None

        full_text = self.alto_client.fetch_content(alto_xml_url)

        if not full_text:
            return None

        return PageContext(
            page_number=int(page_number) if page_number.isdigit() else 0,
            page_id=page_number,
            reference_code=reference_code,
            full_text=full_text,
            alto_url=alto_xml_url,
            image_url=image_url_link or "",
            bildvisning_url=bildvisning_link or "",
        )

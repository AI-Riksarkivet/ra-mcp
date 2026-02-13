"""
Browse operations for viewing document pages.
Handles document browsing, page fetching, and metadata retrieval.
"""

from opentelemetry.trace import StatusCode

from ra_mcp_common.telemetry import get_meter, get_tracer
from ra_mcp_common.utils.http_client import HTTPClient

from .. import url_generator
from ..clients import ALTOClient, IIIFClient, OAIPMHClient
from ..models import BrowseResult, PageContext
from ..utils import parse_page_range


_tracer = get_tracer("ra_mcp.browse_operations")
_meter = get_meter("ra_mcp.browse_operations")
_browse_counter = _meter.create_counter("ra_mcp.browse.requests", description="Browse operations executed")
_pages_histogram = _meter.create_histogram("ra_mcp.browse.pages", description="Pages returned per browse request")
_empty_pages_counter = _meter.create_counter("ra_mcp.browse.empty_pages", description="Blank pages encountered")


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
        highlight_term: str | None = None,
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
        with _tracer.start_as_current_span(
            "BrowseOperations.browse_document",
            attributes={
                "browse.reference_code": reference_code,
                "browse.pages_requested": pages,
            },
        ) as span:
            try:
                # Fetch OAI-PMH metadata once and derive manifest ID from it
                oai_metadata = self.oai_client.get_metadata(reference_code)
                manifest_id = self.oai_client.manifest_id_from_metadata(oai_metadata)

                if not manifest_id:
                    # No manifest = non-digitised material
                    # Return metadata but no page contexts
                    span.set_attribute("browse.pages_returned", 0)
                    _browse_counter.add(1, {"browse.status": "success"})
                    _pages_histogram.record(0)
                    return BrowseResult(
                        contexts=[],
                        reference_code=reference_code,
                        pages_requested=pages,
                        oai_metadata=oai_metadata,
                    )

                page_contexts = self._fetch_page_contexts(manifest_id, pages, max_pages, reference_code, highlight_term)

                # Count empty pages (blank but digitised)
                empty_count = sum(1 for ctx in page_contexts if not ctx.full_text)
                if empty_count:
                    _empty_pages_counter.add(empty_count)

                span.set_attribute("browse.pages_returned", len(page_contexts))
                _browse_counter.add(1, {"browse.status": "success"})
                _pages_histogram.record(len(page_contexts))
                return BrowseResult(
                    contexts=page_contexts,
                    reference_code=reference_code,
                    pages_requested=pages,
                    manifest_id=manifest_id,
                    oai_metadata=oai_metadata,
                )
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                _browse_counter.add(1, {"browse.status": "error"})
                raise

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
        iiif_collection = self.iiif_client.get_collection(persistent_identifier)

        # Return first manifest ID if available, otherwise use PID
        if iiif_collection and iiif_collection.manifests:
            return iiif_collection.manifests[0].id

        return persistent_identifier

    def _fetch_page_contexts(
        self,
        manifest_identifier: str,
        page_specification: str,
        maximum_pages: int,
        reference_code: str,
        highlight_keyword: str | None,
    ) -> list:
        """Fetch page contexts for specified page numbers.

        Retrieves full page content for each specified page number,
        with optional keyword highlighting.

        Early exit optimization: If the first page fails to fetch (404 on ALTO),
        stop attempting subsequent pages since they will also fail for non-transcribed materials.

        Args:
            manifest_identifier: IIIF manifest ID to fetch pages from.
            page_specification: Page range specification (e.g., '1-5,7').
            maximum_pages: Maximum pages to fetch.
            reference_code: Document reference for context.
            highlight_keyword: Optional term to highlight.

        Returns:
            List of page context objects with transcribed text and metadata.
        """
        with _tracer.start_as_current_span(
            "BrowseOperations._fetch_page_contexts",
            attributes={
                "browse.manifest_id": manifest_identifier,
                "browse.page_spec": page_specification,
            },
        ) as span:
            # Parse and limit page numbers
            page_numbers = parse_page_range(page_specification)[:maximum_pages]

            # Fetch context for each page
            page_contexts = []
            consecutive_failures = 0
            MAX_CONSECUTIVE_FAILURES = 3  # Try at least 3 pages before giving up

            for page_number in page_numbers:
                page_context = self._get_page_context(manifest_identifier, str(page_number), reference_code, highlight_keyword)
                if page_context:
                    page_contexts.append(page_context)
                    consecutive_failures = 0  # Reset counter on success
                else:
                    consecutive_failures += 1
                    # Early exit optimization: if first 3 pages all fail with 404, assume not transcribed
                    # Note: blank pages (200 OK but empty) are treated as successful page_context,
                    # so this only exits early when ALTO files don't exist (404 errors)
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES and not page_contexts:
                        break

            span.set_attribute("browse.pages_fetched", len(page_contexts))
            return page_contexts

    def _get_page_context(
        self,
        manifest_id: str,
        page_number: str,
        reference_code: str = "",
        search_term: str | None = None,
    ) -> PageContext | None:
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

        # None = ALTO doesn't exist (404), empty string = ALTO exists but blank page
        if full_text is None:
            return None

        # Allow empty string through - it means the page exists but is blank
        return PageContext(
            page_number=int(page_number) if page_number.isdigit() else 0,
            page_id=page_number,
            reference_code=reference_code,
            full_text=full_text,
            alto_url=alto_xml_url,
            image_url=image_url_link or "",
            bildvisning_url=bildvisning_link or "",
        )

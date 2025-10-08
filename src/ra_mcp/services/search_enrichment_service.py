"""
Service for enriching search hits with full page context.
"""

from collections import defaultdict
from typing import List, Optional, Union

from ..clients import IIIFClient, ALTOClient
from ..utils.http_client import HTTPClient
from ..config import DEFAULT_MAX_PAGES
from ..models import SearchHit
from ..utils import url_generator


class SearchEnrichmentService:
    """Service for enriching search hits with full page context."""

    def __init__(self, http_client: HTTPClient):
        self.iiif_client = IIIFClient(http_client=http_client)
        self.alto_client = ALTOClient(http_client=http_client)

    def enrich_hits_with_context(
        self,
        hits: List[SearchHit],
        max_pages: int = DEFAULT_MAX_PAGES,
        search_term: Optional[str] = None,
    ) -> List[SearchHit]:
        """Enrich search hits with full page context by exploring IIIF collections."""
        grouped_hits_by_pid = self._group_hits_by_persistent_identifier(hits, max_pages)

        enriched_search_results = self._process_grouped_hits(grouped_hits_by_pid, max_pages, search_term)

        return enriched_search_results

    def _group_hits_by_persistent_identifier(self, search_hits: List[SearchHit], maximum_limit: int) -> dict:
        """Group hits by PID to avoid exploring the same collection multiple times."""
        grouped_hits = defaultdict(list)
        limited_hits = search_hits[:maximum_limit]

        for hit in limited_hits:
            grouped_hits[hit.pid].append(hit)

        return grouped_hits

    def _process_grouped_hits(self, grouped_hits: dict, page_limit: int, search_keyword: Optional[str]) -> List[SearchHit]:
        """Process grouped hits and enrich them with context."""
        enriched_results = []
        total_processed_count = 0

        for persistent_id, pid_hit_collection in grouped_hits.items():
            if total_processed_count >= page_limit:
                break

            processed_hits = self._process_hits_for_single_pid(
                persistent_id,
                pid_hit_collection,
                page_limit,
                total_processed_count,
                search_keyword,
            )

            enriched_results.extend(processed_hits)
            total_processed_count += len(processed_hits)

        return enriched_results

    def _process_hits_for_single_pid(
        self,
        persistent_identifier: str,
        hit_collection: List[SearchHit],
        page_limit: int,
        current_processed_count: int,
        search_keyword: Optional[str],
    ) -> List[SearchHit]:
        """Process all hits for a single PID."""
        iiif_collection_data = self.iiif_client.explore_collection(persistent_identifier, timeout=10)

        if self._has_valid_manifests(iiif_collection_data):
            return self._process_hits_with_manifest(
                iiif_collection_data,
                hit_collection,
                page_limit,
                current_processed_count,
                search_keyword,
            )
        else:
            return self._process_hits_without_manifest(
                persistent_identifier,
                hit_collection,
                page_limit,
                current_processed_count,
                search_keyword,
            )

    def _has_valid_manifests(self, collection_data: Optional[dict]) -> bool:
        """Check if collection data contains valid manifests."""
        return bool(collection_data and collection_data.get("manifests"))

    def _process_hits_with_manifest(
        self,
        collection_data: dict,
        hit_collection: List[SearchHit],
        page_limit: int,
        current_count: int,
        search_keyword: Optional[str],
    ) -> List[SearchHit]:
        """Process hits when manifest is available."""
        first_manifest = collection_data["manifests"][0]
        manifest_identifier = first_manifest["id"]

        processed_results = []
        remaining_capacity = page_limit - current_count

        for hit in hit_collection:
            if len(processed_results) >= remaining_capacity:
                break

            enriched_hit = self._enrich_hit_with_manifest(hit, manifest_identifier, search_keyword)
            processed_results.append(enriched_hit)

        return processed_results

    def _process_hits_without_manifest(
        self,
        persistent_identifier: str,
        hit_collection: List[SearchHit],
        page_limit: int,
        current_count: int,
        search_keyword: Optional[str],
    ) -> List[SearchHit]:
        """Process hits when no manifest is available.

        Without a manifest, we cannot generate valid ALTO URLs,
        so we only provide snippet text and basic URLs.
        """
        processed_results = []
        remaining_capacity = page_limit - current_count

        for hit in hit_collection:
            if len(processed_results) >= remaining_capacity:
                break

            # Without manifest, we can't generate ALTO URLs
            # Only set image and bildvisning URLs using the PID
            hit.image_url = url_generator.iiif_image_url(persistent_identifier, hit.page_number)
            hit.bildvisning_url = url_generator.bildvisning_url(persistent_identifier, hit.page_number, search_keyword)
            # Use snippet text since we can't fetch ALTO content
            hit.full_page_text = hit.snippet_text
            processed_results.append(hit)

        return processed_results

    def _enrich_hit_with_manifest(
        self,
        search_hit: SearchHit,
        manifest_identifier: str,
        search_keyword: Optional[str],
    ) -> SearchHit:
        """Enrich a single hit with manifest data and ALTO content."""
        self._enrich_single_hit(search_hit, manifest_identifier, search_keyword)

        full_page_content = self._fetch_alto_content_for_hit(search_hit)
        search_hit.full_page_text = full_page_content or search_hit.snippet_text

        return search_hit

    def _fetch_alto_content_for_hit(self, search_hit: SearchHit) -> Optional[str]:
        """Fetch ALTO content for a search hit."""
        if not search_hit.alto_url:
            return None

        alto_text_content = self.alto_client.fetch_content(search_hit.alto_url, timeout=8)

        return alto_text_content

    def _enrich_single_hit(
        self,
        search_hit: SearchHit,
        manifest_identifier: str,
        search_keyword: Optional[str],
    ):
        """Enrich a single hit with generated URLs."""
        # Clean the manifest identifier for ALTO URL (remove arkis! prefix if present)
        clean_manifest_id = url_generator.remove_arkis_prefix(manifest_identifier)
        search_hit.alto_url = url_generator.alto_url(clean_manifest_id, search_hit.page_number)
        search_hit.image_url = url_generator.iiif_image_url(manifest_identifier, search_hit.page_number)
        search_hit.bildvisning_url = url_generator.bildvisning_url(manifest_identifier, search_hit.page_number, search_keyword)

    def expand_hits_with_context_padding(self, hits: List[SearchHit], padding: int = 1) -> List[SearchHit]:
        """Expand search hits with context pages around each hit."""
        if padding <= 0:
            return hits

        grouped_document_hits = self._group_hits_by_document(hits)
        expanded_search_results = self._build_expanded_hit_collection(grouped_document_hits, padding)

        sorted_results = self._sort_hits_by_document_order(expanded_search_results)
        return sorted_results

    def _group_hits_by_document(self, search_hits: List[SearchHit]) -> dict:
        """Group hits by PID and reference code."""
        document_grouped_hits = defaultdict(list)

        for hit in search_hits:
            document_key = (hit.pid, hit.reference_code)
            document_grouped_hits[document_key].append(hit)

        return document_grouped_hits

    def _build_expanded_hit_collection(self, grouped_documents: dict, context_padding: int) -> List[SearchHit]:
        """Build expanded collection with context pages."""
        expanded_results = []

        for document_identifiers, document_hits in grouped_documents.items():
            persistent_id, reference_code = document_identifiers

            document_page_numbers = self._extract_page_numbers_from_hits(document_hits)

            context_page_set = self._generate_context_pages(document_page_numbers, context_padding)

            expanded_document_hits = self._create_hits_for_all_pages(persistent_id, reference_code, context_page_set, document_hits)

            expanded_results.extend(expanded_document_hits)

        return expanded_results

    def _extract_page_numbers_from_hits(self, document_hits: List[SearchHit]) -> set:
        """Extract all page numbers from document hits."""
        page_number_set = set()

        for hit in document_hits:
            parsed_page = self._parse_page_number(hit.page_number)
            page_number_set.add(parsed_page)

        return page_number_set

    def _parse_page_number(self, page_number_string: str) -> Union[int, str]:
        """Parse page number string to integer or keep as string."""
        try:
            stripped_number = page_number_string.lstrip("0")
            if stripped_number.isdigit():
                return int(stripped_number)
            return int(page_number_string)
        except (ValueError, AttributeError):
            return page_number_string

    def _generate_context_pages(self, original_pages: set, padding_size: int) -> set:
        """Generate context pages around original pages."""
        context_page_collection = set()

        for page_identifier in original_pages:
            if isinstance(page_identifier, int):
                padded_pages = self._calculate_padded_pages(page_identifier, padding_size)
                context_page_collection.update(padded_pages)
            else:
                context_page_collection.add(page_identifier)

        return context_page_collection

    def _calculate_padded_pages(self, center_page: int, padding_range: int) -> set:
        """Calculate padded pages around a center page."""
        padded_page_set = set()

        for offset in range(-padding_range, padding_range + 1):
            padded_page = center_page + offset
            if padded_page > 0:
                padded_page_set.add(padded_page)

        return padded_page_set

    def _create_hits_for_all_pages(
        self,
        persistent_identifier: str,
        reference_code: str,
        all_pages: set,
        existing_hits: List[SearchHit],
    ) -> List[SearchHit]:
        """Create SearchHit objects for all pages."""
        page_hits = []

        for page_identifier in all_pages:
            existing_hit = self._find_existing_hit(existing_hits, page_identifier)

            if existing_hit:
                page_hits.append(existing_hit)
            else:
                context_hit = self._create_context_hit(
                    persistent_identifier,
                    reference_code,
                    page_identifier,
                    existing_hits,
                )
                page_hits.append(context_hit)

        return page_hits

    def _sort_hits_by_document_order(self, hit_collection: List[SearchHit]) -> List[SearchHit]:
        """Sort hits by PID, reference code, and page number."""
        return sorted(hit_collection, key=self._sort_key)

    def _find_existing_hit(self, document_hits: List[SearchHit], target_page: Union[int, str]) -> Optional[SearchHit]:
        """Find existing hit for a given page."""
        for hit in document_hits:
            if self._page_matches_hit(target_page, hit):
                return hit
        return None

    def _page_matches_hit(self, target_page: Union[int, str], search_hit: SearchHit) -> bool:
        """Check if target page matches the hit's page number."""
        hit_page_normalized = self._normalize_page_for_comparison(search_hit.page_number)

        try:
            if isinstance(target_page, int):
                return int(hit_page_normalized) == target_page
            return str(target_page) == search_hit.page_number
        except (ValueError, AttributeError):
            return str(target_page) == search_hit.page_number

    def _normalize_page_for_comparison(self, page_number: str) -> str:
        """Normalize page number for comparison."""
        stripped_page = page_number.lstrip("0")
        return stripped_page if stripped_page.isdigit() else page_number

    def _create_context_hit(
        self,
        persistent_identifier: str,
        reference_code: str,
        page_identifier: Union[int, str],
        existing_document_hits: List[SearchHit],
    ) -> SearchHit:
        """Create a context hit for a page that doesn't have search results."""
        formatted_page_number = self._format_page_number(page_identifier)
        template_hit = self._get_template_hit(existing_document_hits)

        return self._build_context_hit_from_template(persistent_identifier, reference_code, formatted_page_number, template_hit)

    def _format_page_number(self, page_identifier: Union[int, str]) -> str:
        """Format page identifier as string."""
        if isinstance(page_identifier, int):
            return f"{page_identifier:05d}"
        return str(page_identifier)

    def _get_template_hit(self, document_hits: List[SearchHit]) -> Optional[SearchHit]:
        """Get template hit for metadata copying."""
        return document_hits[0] if document_hits else None

    def _build_context_hit_from_template(
        self,
        persistent_identifier: str,
        reference_code: str,
        page_number: str,
        template: Optional[SearchHit],
    ) -> SearchHit:
        """Build context hit using template metadata."""
        return SearchHit(
            pid=persistent_identifier,
            title=template.title if template else "(No title)",
            reference_code=reference_code,
            page_number=page_number,
            snippet_text="[Context page - no search hit]",
            score=0.0,
            hierarchy=template.hierarchy if template else None,
            note=template.note if template else None,
            collection_url=template.collection_url if template else None,
            manifest_url=template.manifest_url if template else None,
            archival_institution=template.archival_institution if template else None,
            date=template.date if template else None,
        )

    def _sort_key(self, search_hit: SearchHit):
        """Sort key for organizing hits."""
        parsed_page_number = self._extract_numeric_page_for_sorting(search_hit.page_number)
        return (search_hit.pid, search_hit.reference_code, parsed_page_number)

    def _extract_numeric_page_for_sorting(self, page_number: str) -> int:
        """Extract numeric page number for sorting."""
        try:
            stripped_page = page_number.lstrip("0")
            if stripped_page.isdigit():
                return int(stripped_page)
            return 999999
        except (ValueError, AttributeError):
            return 999999

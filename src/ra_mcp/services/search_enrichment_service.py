"""
Service for enriching search hits with full page context.
"""

from collections import defaultdict
from typing import List, Optional

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

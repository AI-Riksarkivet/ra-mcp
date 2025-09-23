"""
Service for enriching search hits with full page context.
"""

from collections import defaultdict
from typing import List, Optional

from ..clients import IIIFClient, ALTOClient
from ..config import DEFAULT_MAX_PAGES
from ..models import SearchHit
from ..utils import URLGenerator


class SearchEnrichmentService:
    """Service for enriching search hits with full page context."""

    def __init__(self):
        self.iiif_client = IIIFClient()
        self.alto_client = ALTOClient()

    def enrich_hits_with_context(
        self,
        hits: List[SearchHit],
        max_pages: int = DEFAULT_MAX_PAGES,
        search_term: Optional[str] = None
    ) -> List[SearchHit]:
        """Enrich search hits with full page context by exploring IIIF collections."""
        enriched_hits = []
        processed = 0
        failed = 0

        # Group hits by PID to avoid exploring the same collection multiple times
        hits_by_pid = defaultdict(list)
        for hit in hits[:max_pages]:
            hits_by_pid[hit.pid].append(hit)

        # Simplified processing without progress display
        for pid, pid_hits in hits_by_pid.items():
            if processed >= max_pages:
                break

            # Explore the IIIF collection to get manifest IDs
            collection_info = self.iiif_client.explore_collection(pid, timeout=10)

            if collection_info and collection_info.get('manifests'):
                manifest = collection_info['manifests'][0]
                manifest_id = manifest['id']

                # Process each hit for this PID
                for hit in pid_hits:
                    if processed >= max_pages:
                        break

                    page_ref = f"{hit.reference_code or hit.pid[-8:]}:p{hit.page_number}"
                    self._enrich_single_hit(hit, manifest_id, search_term)

                    # Try to get ALTO content
                    if hit.alto_url:
                        full_text = self.alto_client.fetch_content(hit.alto_url, timeout=8)
                        if full_text:
                            hit.full_page_text = full_text
                        else:
                            hit.full_page_text = hit.snippet_text
                    else:
                        hit.full_page_text = hit.snippet_text

                    enriched_hits.append(hit)
                    processed += 1
            else:
                # No manifests found, fall back to snippet text
                for hit in pid_hits:
                    if processed >= max_pages:
                        break
                    self._enrich_single_hit(hit, hit.pid, search_term)
                    hit.full_page_text = hit.snippet_text
                    enriched_hits.append(hit)
                    processed += 1
                    failed += 1

        # Return enriched hits without console output
        return enriched_hits

    def _enrich_single_hit(self, hit: SearchHit, manifest_id: str, search_term: Optional[str]):
        """Enrich a single hit with generated URLs."""
        hit.alto_url = URLGenerator.alto_url(manifest_id, hit.page_number)
        hit.image_url = URLGenerator.iiif_image_url(manifest_id, hit.page_number)
        hit.bildvisning_url = URLGenerator.bildvisning_url(manifest_id, hit.page_number, search_term)

    def expand_hits_with_context_padding(self, hits: List[SearchHit], padding: int = 1) -> List[SearchHit]:
        """Expand search hits with context pages around each hit."""
        if padding <= 0:
            return hits

        # Group hits by PID and reference code
        hits_by_doc = defaultdict(list)
        for hit in hits:
            key = (hit.pid, hit.reference_code)
            hits_by_doc[key].append(hit)

        expanded_hits = []

        for (pid, ref_code), doc_hits in hits_by_doc.items():
            # Get all page numbers for this document
            hit_pages = set()
            for hit in doc_hits:
                try:
                    page_num = int(hit.page_number.lstrip('0')) if hit.page_number.lstrip('0').isdigit() else int(hit.page_number)
                    hit_pages.add(page_num)
                except (ValueError, AttributeError):
                    hit_pages.add(hit.page_number)

            # Generate context pages around each hit
            context_pages = set()
            for page in hit_pages:
                if isinstance(page, int):
                    for offset in range(-padding, padding + 1):
                        context_page = page + offset
                        if context_page > 0:
                            context_pages.add(context_page)
                else:
                    context_pages.add(page)

            # Create SearchHit objects for all context pages
            for page in context_pages:
                existing_hit = self._find_existing_hit(doc_hits, page)
                if existing_hit:
                    expanded_hits.append(existing_hit)
                else:
                    context_hit = self._create_context_hit(pid, ref_code, page, doc_hits)
                    expanded_hits.append(context_hit)

        # Sort by PID, reference code, and page number
        expanded_hits.sort(key=self._sort_key)
        return expanded_hits

    def _find_existing_hit(self, doc_hits: List[SearchHit], page) -> Optional[SearchHit]:
        """Find existing hit for a given page."""
        for hit in doc_hits:
            hit_page_num = hit.page_number.lstrip('0') if hit.page_number.lstrip('0').isdigit() else hit.page_number
            try:
                if isinstance(page, int) and int(hit_page_num) == page:
                    return hit
                elif str(page) == hit.page_number:
                    return hit
            except (ValueError, AttributeError):
                if str(page) == hit.page_number:
                    return hit
        return None

    def _create_context_hit(self, pid: str, ref_code: str, page, doc_hits: List[SearchHit]) -> SearchHit:
        """Create a context hit for a page that doesn't have search results."""
        page_str = f"{page:05d}" if isinstance(page, int) else str(page)
        template_hit = doc_hits[0] if doc_hits else None

        return SearchHit(
            pid=pid,
            title=template_hit.title if template_hit else "(No title)",
            reference_code=ref_code,
            page_number=page_str,
            snippet_text="[Context page - no search hit]",
            score=0.0,
            hierarchy=template_hit.hierarchy if template_hit else None,
            note=template_hit.note if template_hit else None,
            collection_url=template_hit.collection_url if template_hit else None,
            manifest_url=template_hit.manifest_url if template_hit else None,
            archival_institution=template_hit.archival_institution if template_hit else None,
            date=template_hit.date if template_hit else None
        )

    @staticmethod
    def _sort_key(hit: SearchHit):
        """Sort key for organizing hits."""
        try:
            page_num = int(hit.page_number.lstrip('0')) if hit.page_number.lstrip('0').isdigit() else 999999
        except (ValueError, AttributeError):
            page_num = 999999
        return (hit.pid, hit.reference_code, page_num)
"""
Service for getting full page context.
"""

from typing import Optional

from ..clients import ALTOClient, OAIPMHClient
from ..models import PageContext
from ..utils import url_generator
from ..utils.http_client import HTTPClient


class PageContextService:
    """Service for getting full page context."""

    def __init__(self, http_client: HTTPClient):
        self.alto_client = ALTOClient(http_client=http_client)
        self.oai_client = OAIPMHClient(http_client=http_client)

    def get_page_context(
        self,
        manifest_id: str,
        page_number: str,
        reference_code: str = "",
        search_term: Optional[str] = None,
    ) -> Optional[PageContext]:
        """Get full page context for a specific page using manifest ID for ALTO URL generation"""

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

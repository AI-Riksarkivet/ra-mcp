"""
Service for getting full page context.
"""

from typing import Optional

from ..clients import ALTOClient
from ..models import PageContext
from ..utils import URLGenerator


class PageContextService:
    """Service for getting full page context."""

    def __init__(self):
        self.alto_client = ALTOClient()

    def get_page_context(
        self,
        pid: str,
        page_number: str,
        reference_code: str = "",
        search_term: Optional[str] = None,
    ) -> Optional[PageContext]:
        """Get full page context for a specific page."""
        alto_url = URLGenerator.alto_url(pid, page_number)
        image_url = URLGenerator.iiif_image_url(pid, page_number)
        bildvisning_url = URLGenerator.bildvisning_url(pid, page_number, search_term)

        if not alto_url:
            return None

        full_text = self.alto_client.fetch_content(alto_url)
        if not full_text:
            return None

        return PageContext(
            page_number=int(page_number) if page_number.isdigit() else 0,
            page_id=page_number,
            reference_code=reference_code,
            full_text=full_text,
            alto_url=alto_url,
            image_url=image_url or "",
            bildvisning_url=bildvisning_url or "",
        )

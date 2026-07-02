"""
Data models for Riksarkivet browse operations.

Models for browsing document pages with full text and metadata.
"""

from pydantic import BaseModel

from ra_mcp_oai_pmh_lib import OAIPMHMetadata


class PageContext(BaseModel):
    """
    Full page context for browsing.

    Contains transcribed text, ALTO XML URL, and image URLs for a single page.
    """

    page_number: int
    page_id: str
    reference_code: str
    full_text: str  # Extracted from ALTO XML
    alto_url: str  # Client-generated URL to ALTO XML
    image_url: str  # Client-generated IIIF image URL
    bildvisning_url: str = ""  # Client-generated bildvisning URL


class BrowseResult(BaseModel):
    """
    Result from browsing document pages.

    Contains page contexts, manifest ID, and optional OAI-PMH metadata.
    """

    contexts: list[PageContext]
    reference_code: str
    pages_requested: str
    manifest_id: str | None = None  # IIIF manifest ID (e.g., "R0001203")
    oai_metadata: OAIPMHMetadata | None = None  # Metadata from OAI-PMH API

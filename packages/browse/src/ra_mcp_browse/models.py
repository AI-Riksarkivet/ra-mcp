"""
Data models for Riksarkivet browse operations.

Models for browsing document pages with full text and metadata.
"""

from typing import List, Optional
from pydantic import BaseModel


class IIIFManifest(BaseModel):
    """IIIF manifest reference."""

    id: str
    label: Optional[str] = None


class IIIFCollection(BaseModel):
    """IIIF collection information."""

    id: str
    label: Optional[str] = None
    manifests: List[IIIFManifest] = []


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


class OAIPMHMetadata(BaseModel):
    """
    Document metadata from OAI-PMH GetRecord response.

    Maps to EAD metadata fields returned by the OAI-PMH API.
    """

    identifier: str  # Record identifier (e.g., "SE/RA/310187/1")
    title: Optional[str] = None  # EAD unittitle
    unitid: Optional[str] = None  # EAD unitid
    repository: Optional[str] = None  # EAD repository name
    nad_link: Optional[str] = None  # Link to bildvisning (dao[@xlink:role="TEXT"])
    datestamp: Optional[str] = None  # Last modified timestamp
    unitdate: Optional[str] = None  # EAD unitdate - date range of the document
    description: Optional[str] = None  # EAD scopecontent - detailed description
    iiif_manifest: Optional[str] = None  # IIIF manifest URL (dao[@xlink:role="MANIFEST"])
    iiif_image: Optional[str] = None  # Direct IIIF image URL (dao[@xlink:role="IMAGE"])


class BrowseResult(BaseModel):
    """
    Result from browsing document pages.

    Contains page contexts, manifest ID, and optional OAI-PMH metadata.
    """

    contexts: List[PageContext]
    reference_code: str
    pages_requested: str
    manifest_id: Optional[str] = None  # IIIF manifest ID (e.g., "R0001203")
    oai_metadata: Optional[OAIPMHMetadata] = None  # Metadata from OAI-PMH API

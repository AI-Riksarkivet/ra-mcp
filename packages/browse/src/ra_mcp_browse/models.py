"""
Data models for Riksarkivet browse operations.

Models for browsing document pages with full text and metadata.
"""

from pydantic import BaseModel


class IIIFManifest(BaseModel):
    """IIIF manifest reference."""

    id: str
    label: str | None = None


class IIIFCollection(BaseModel):
    """IIIF collection information."""

    id: str
    label: str | None = None
    manifests: list[IIIFManifest] = []


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
    title: str | None = None  # EAD unittitle
    unitid: str | None = None  # EAD unitid
    repository: str | None = None  # EAD repository name
    nad_link: str | None = None  # Link to bildvisning (dao[@xlink:role="TEXT"])
    datestamp: str | None = None  # Last modified timestamp
    unitdate: str | None = None  # EAD unitdate - date range of the document
    description: str | None = None  # EAD scopecontent - detailed description
    iiif_manifest: str | None = None  # IIIF manifest URL (dao[@xlink:role="MANIFEST"])
    iiif_image: str | None = None  # Direct IIIF image URL (dao[@xlink:role="IMAGE"])


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

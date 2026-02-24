"""Data models for OAI-PMH metadata."""

from pydantic import BaseModel


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

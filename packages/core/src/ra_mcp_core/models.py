"""
Data models for Riksarkivet MCP server.

Models are designed to closely match the API JSON structure while providing
convenient access to search results and browse operations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# API Response Models (matching Riksarkivet Search API structure)
# ============================================================================

class ArchivalInstitution(BaseModel):
    """Archival institution information."""
    caption: str
    uri: str


class HierarchyLevel(BaseModel):
    """Hierarchy level in archival structure."""
    caption: str
    uri: str


class Provenance(BaseModel):
    """Provenance information."""
    caption: str
    uri: str
    date: Optional[str] = None


class Metadata(BaseModel):
    """Document metadata from API."""
    model_config = ConfigDict(populate_by_name=True)

    reference_code: str = Field(alias="referenceCode")
    date: Optional[str] = None
    hierarchy: Optional[List[HierarchyLevel]] = None
    archival_institution: Optional[List[ArchivalInstitution]] = Field(None, alias="archivalInstitution")
    provenance: Optional[List[Provenance]] = None
    note: Optional[str] = None
    only_digitised_materials: Optional[bool] = Field(None, alias="onlyDigitisedMaterials")


class PageInfo(BaseModel):
    """Page information from snippet."""
    id: str
    width: Optional[int] = None
    height: Optional[int] = None


class Snippet(BaseModel):
    """Text snippet with search match."""
    text: str
    score: float
    pages: List[PageInfo]
    regions: Optional[List[Any]] = None
    highlights: Optional[List[Any]] = None


class TranscribedText(BaseModel):
    """Transcribed text information."""
    num_total: int = Field(alias="numTotal")
    snippets: List[Snippet]

    model_config = ConfigDict(populate_by_name=True)
    


class DocumentLinks(BaseModel):
    """Links from API _links field."""
    self: Optional[str] = None
    html: Optional[str] = None
    image: Optional[List[str]] = None
    rdf_xml: Optional[str] = Field(None, alias="rdf/xml")
    json_ld: Optional[str] = Field(None, alias="json-ld")
    ead_ra: Optional[str] = Field(None, alias="ead/ra")
    ead_ape: Optional[str] = Field(None, alias="ead/ape")

    model_config = ConfigDict(populate_by_name=True)
    


class SearchRecord(BaseModel):
    """Record from search API matching JSON structure (objectType: Record, type: Volume)."""
    id: str
    object_type: str = Field(alias="objectType")
    type: str
    caption: Optional[str] = None
    metadata: Metadata
    transcribed_text: Optional[TranscribedText] = Field(None, alias="transcribedText")
    links: Optional[DocumentLinks] = Field(None, alias="_links")

    model_config = ConfigDict(populate_by_name=True)
    

    def get_manifest_url(self) -> Optional[str]:
        """Get manifest URL from links."""
        if self.links and self.links.image:
            return self.links.image[0] if self.links.image else None
        return None

    def get_collection_url(self) -> str:
        """Get collection URL for this document."""
        return f"https://lbiiif.riksarkivet.se/arkis/{self.id}"

    def get_title(self) -> str:
        """Get document title or default."""
        return self.caption or "(No title)"

    def get_total_hits(self) -> int:
        """Get total number of hits in this document."""
        return self.transcribed_text.num_total if self.transcribed_text else 0

    def get_snippet_count(self) -> int:
        """Get number of snippets returned for this document."""
        return len(self.transcribed_text.snippets) if self.transcribed_text else 0


# ============================================================================
# Search Results Container
# ============================================================================

class SearchResult(BaseModel):
    """Container for search results."""
    documents: List[SearchRecord]
    total_hits: int
    keyword: str
    offset: int

    def extract_summary(self) -> "SearchSummary":
        """Extract summary information from search results.

        Returns:
            SearchSummary with statistics about the search results.
        """
        # Count total page hits across all documents
        total_page_hits = sum(doc.get_snippet_count() for doc in self.documents)

        return SearchSummary(
            keyword=self.keyword,
            total_hits=self.total_hits,
            page_hits_returned=total_page_hits,
            documents_returned=len(self.documents),
            offset=self.offset,
            documents=self.documents,
        )


class SearchSummary(BaseModel):
    """Summary information from a search operation."""
    keyword: str
    total_hits: int
    page_hits_returned: int
    documents_returned: int
    offset: int
    documents: List[SearchRecord]


# ============================================================================
# Browse Results Models
# ============================================================================

class PageContext(BaseModel):
    """Full page context for browsing."""
    page_number: int
    page_id: str
    reference_code: str
    full_text: str
    alto_url: str
    image_url: str
    bildvisning_url: str = ""


class DocumentMetadata(BaseModel):
    """Document metadata for browse operations."""
    title: Optional[str] = None
    hierarchy: Optional[List[Dict[str, str]]] = None
    archival_institution: Optional[List[Dict[str, str]]] = None
    date: Optional[str] = None
    note: Optional[str] = None
    collection_url: Optional[str] = None
    manifest_url: Optional[str] = None


class BrowseResult(BaseModel):
    """Result from browsing document pages."""
    contexts: List[PageContext]
    reference_code: str
    pages_requested: str
    manifest_id: Optional[str] = None
    document_metadata: Optional[DocumentMetadata] = None

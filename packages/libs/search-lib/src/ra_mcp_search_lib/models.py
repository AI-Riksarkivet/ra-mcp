"""
Data models for Riksarkivet search operations.

Models are designed to closely match the Search API JSON structure.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# API Response Models (matching Riksarkivet Search API structure)
# ============================================================================


class GenericReference(BaseModel):
    """Generic reference (archival institution, hierarchy level, provenance).

    Maps to the GenericReference type in the Swagger spec. All fields are nullable.
    """

    caption: str | None = None
    uri: str | None = None
    date: str | None = None


class Metadata(BaseModel):
    """Document metadata from API."""

    model_config = ConfigDict(populate_by_name=True)

    reference_code: str | None = Field(None, alias="referenceCode")
    date: str | None = None
    hierarchy: list[GenericReference] | None = None
    part_of: list[GenericReference] | None = Field(None, alias="partOf")
    archival_institution: list[GenericReference] | None = Field(None, alias="archivalInstitution")
    provenance: list[GenericReference] | None = None
    note: str | None = None
    only_digitised_materials: bool | None = Field(None, alias="onlyDigitisedMaterials")


class PageInfo(BaseModel):
    """Page information from snippet.

    Note: id is marked nullable in the Swagger spec but is always present
    in search results. We default to "" for safety.
    """

    id: str = ""
    width: int | None = None
    height: int | None = None


class Snippet(BaseModel):
    """Text snippet with search match.

    Note: text and pages are marked nullable in the Swagger spec but are
    always present in search results. We use safe defaults.
    """

    text: str = ""
    score: float = 0.0
    pages: list[PageInfo] = Field(default_factory=list)
    regions: list[Any] | None = None
    highlights: list[Any] | None = None


class TranscribedText(BaseModel):
    """Transcribed text information.

    Note: snippets is marked nullable in the Swagger spec but is always
    present (possibly empty) in search results.
    """

    num_total: int = Field(alias="numTotal")
    snippets: list[Snippet] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class DocumentLinks(BaseModel):
    """Links from API _links field."""

    self: str | None = None
    html: str | None = None
    image: list[str] | None = None
    rdf_xml: str | None = Field(None, alias="rdf/xml")
    json_ld: str | None = Field(None, alias="json-ld")
    ead_ra: str | None = Field(None, alias="ead/ra")
    ead_ape: str | None = Field(None, alias="ead/ape")

    model_config = ConfigDict(populate_by_name=True)


class SearchRecord(BaseModel):
    """Record from search API matching JSON structure (objectType: Record, type: Volume)."""

    id: str
    object_type: str = Field(alias="objectType")
    type: str | None = None
    caption: str | None = None
    metadata: Metadata
    transcribed_text: TranscribedText | None = Field(None, alias="transcribedText")
    links: DocumentLinks | None = Field(None, alias="_links")

    model_config = ConfigDict(populate_by_name=True)

    def get_manifest_url(self) -> str | None:
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
# API Search Response
# ============================================================================


class RecordsResponse(BaseModel):
    """
    Search API response matching /api/records endpoint.

    Maps to the full API response structure from /api/records.
    """

    items: list[SearchRecord]
    total_hits: int = Field(alias="totalHits")
    hits: int | None = None  # Number of records returned in this response
    offset: int | None = None  # Pagination offset from query
    facets: list[dict[str, Any]] | None = None  # Faceted search results (list of facet objects)
    links: dict[str, str] | None = Field(None, alias="_links")  # HATEOAS links

    model_config = ConfigDict(populate_by_name=True)

    def count_snippets(self) -> int:
        """Count total snippets across all records."""
        return sum(record.get_snippet_count() for record in self.items)


class SearchResult(BaseModel):
    """
    Search result with query context.

    Wraps RecordsResponse with the search parameters used to execute the search.
    Parameter names match the Search API specification.
    """

    response: RecordsResponse
    transcribed_text: str  # Search keyword (API parameter name)
    limit: int  # Maximum results per page (API parameter name)
    offset: int  # Pagination offset (API parameter name)
    max_snippets_per_record: int | None = None  # Client-side snippet limiting (not an API parameter)

    @property
    def items(self) -> list[SearchRecord]:
        """Get records from response."""
        return self.response.items

    @property
    def total_hits(self) -> int:
        """Get total hits from response."""
        return self.response.total_hits

    @property
    def keyword(self) -> str:
        """Alias for transcribed_text for backward compatibility."""
        return self.transcribed_text

    def count_snippets(self) -> int:
        """Count total snippets across all records."""
        return self.response.count_snippets()

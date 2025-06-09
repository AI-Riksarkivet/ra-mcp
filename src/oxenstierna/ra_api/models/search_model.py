from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ObjectType(str, Enum):
    """Available object types for filtering."""

    RECORD_SET = "RecordSet"  # Archive record, collection
    RECORD = "Record"  # Archive record, single
    AGENT = "Agent"  # Authority
    TOPOGRAPHY = "Topography"  # Place


class SortOption(str, Enum):
    """Available sorting options."""

    RELEVANCE = "relevance"
    ALPHA_ASC = "alphaAsc"  # A-Ö
    ALPHA_DESC = "alphaDesc"  # Ö-A
    TIME_ASC = "timeAsc"  # Oldest first
    TIME_DESC = "timeDesc"  # Newest first


class Provenance(str, Enum):
    """Authority categories for provenance."""

    GOVERNMENT_AUTHORITY = "GovernmentAuthority"
    MUNICIPAL_AUTHORITY = "MunicipalAuthority"
    COMPANY = "Company"
    ASSOCIATION = "Association"
    VILLAGE = "Village"
    HOMESTEAD = "Homestead"
    PERSON = "Person"
    OTHER = "Other"
    UNSPECIFIED = "Unspecified"


class FacetValue(BaseModel):
    """A facet value with hit count and URL."""

    value: str = Field(description="The facet value")
    hits: int = Field(description="Number of hits with this value")
    url: str = Field(description="API URL to filter by this facet value")
    sub_facets: Optional[List[FacetValue]] = Field(
        None, description="Sub-facets if available"
    )


class Facet(BaseModel):
    """A search facet with available values."""

    name: str = Field(description="Facet name (ObjectType, Type, etc.)")
    values: List[FacetValue] = Field(description="Available facet values")


class Hierarchy(BaseModel):
    """Hierarchy information for archive records."""

    caption: str = Field(description="Name/title of the hierarchy level")
    uri: str = Field(description="Linked data URI")
    date: Optional[str] = Field(None, description="Dating information")


class Metadata(BaseModel):
    """Metadata for search results."""

    reference_code: Optional[str] = Field(None, description="Reference code")
    hierarchy: Optional[List[Hierarchy]] = Field(None, description="Archive hierarchy")
    provenance: Optional[List[Hierarchy]] = Field(
        None, description="Provenance information"
    )
    archival_institution: Optional[List[Hierarchy]] = Field(
        None, description="Holding institution"
    )
    date: Optional[str] = Field(None, description="Dating (not normalized)")
    note: Optional[str] = Field(None, description="Additional notes")
    part_of: Optional[List[Hierarchy]] = Field(
        None, description="Superior topographies"
    )


class SearchResult(BaseModel):
    """A single search result from the Riksarkivet Search API."""

    id: str = Field(description="PID/UUID for this result")
    object_type: str = Field(description="Type of object (Agent, Archive, etc.)")
    type: str = Field(description="Specific type (FormerOrganization, etc.)")
    caption: str = Field(description="Title/caption of the result")
    reference_code: Optional[str] = Field(
        None, description="Reference code if available"
    )
    metadata: Optional[Metadata] = Field(None, description="Detailed metadata")
    links: Optional[Dict[str, str]] = Field(
        None, description="Links to different representations"
    )

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "SearchResult":
        """Create SearchResult from API response item."""
        metadata_data = data.get("metadata", {})
        metadata = None
        reference_code = None

        if metadata_data:
            reference_code = metadata_data.get("referenceCode")
            metadata = Metadata(
                reference_code=reference_code,
                hierarchy=[
                    Hierarchy(
                        caption=h.get("caption", ""),
                        uri=h.get("uri", ""),
                        date=h.get("date"),
                    )
                    for h in metadata_data.get("hierarchy", [])
                ],
                provenance=[
                    Hierarchy(
                        caption=p.get("caption", ""),
                        uri=p.get("uri", ""),
                        date=p.get("date"),
                    )
                    for p in metadata_data.get("provenance", [])
                ],
                archival_institution=[
                    Hierarchy(
                        caption=ai.get("caption", ""),
                        uri=ai.get("uri", ""),
                        date=ai.get("date"),
                    )
                    for ai in metadata_data.get("archivalInstitution", [])
                ],
                date=metadata_data.get("date"),
                note=metadata_data.get("note"),
                part_of=[
                    Hierarchy(
                        caption=po.get("caption", ""),
                        uri=po.get("uri", ""),
                        date=po.get("date"),
                    )
                    for po in metadata_data.get("partOf", [])
                ],
            )

        return cls(
            id=data.get("id", ""),
            object_type=data.get("objectType", ""),
            type=data.get("type", ""),
            caption=data.get("caption", ""),
            reference_code=reference_code,
            metadata=metadata,
            links=data.get("_links", {}),
        )


class SearchResults(BaseModel):
    """Search results from the Riksarkivet Search API."""

    total_hits: int = Field(description="Total number of hits")
    hits: int = Field(description="Number of hits returned")
    offset: int = Field(description="Offset for pagination")
    query: str = Field(description="Original search query")
    results: List[SearchResult] = Field(description="List of search results")
    facets: List[Facet] = Field(
        default_factory=list, description="Available facets for filtering"
    )
    links: Optional[Dict[str, str]] = Field(None, description="Pagination links")

    @classmethod
    def from_api_response(cls, query: str, data: Dict[str, Any]) -> "SearchResults":
        """Create SearchResults from API response."""
        results = [
            SearchResult.from_api_response(item) for item in data.get("items", [])
        ]

        facets = []
        for facet_data in data.get("facets", []):
            facet_values = []
            for value_data in facet_data.get("values", []):
                sub_facets = None
                if "subFacets" in value_data:
                    sub_facets = [
                        FacetValue(
                            value=sf.get("value", ""),
                            hits=sf.get("hits", 0),
                            url=sf.get("url", ""),
                        )
                        for sf in value_data["subFacets"]
                    ]

                facet_values.append(
                    FacetValue(
                        value=value_data.get("value", ""),
                        hits=value_data.get("hits", 0),
                        url=value_data.get("url", ""),
                        sub_facets=sub_facets,
                    )
                )

            facets.append(Facet(name=facet_data.get("name", ""), values=facet_values))

        return cls(
            total_hits=data.get("totalHits", 0),
            hits=data.get("hits", 0),
            offset=data.get("offset", 0),
            query=query,
            results=results,
            facets=facets,
            links=data.get("_links", {}),
        )

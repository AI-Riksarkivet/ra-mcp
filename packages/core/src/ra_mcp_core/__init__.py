"""
RA-MCP Core: Core library for Riksarkivet MCP Server.

Provides shared models and utilities for all ra-mcp packages.
"""

__version__ = "0.2.7"

from .models import (
    # API Response Models
    ArchivalInstitution,
    HierarchyLevel,
    Provenance,
    Metadata,
    PageInfo,
    Snippet,
    TranscribedText,
    DocumentLinks,
    SearchRecord,
    RecordsResponse,
    # Search Results
    SearchResult,
    # Browse Results
    PageContext,
    OAIPMHMetadata,
    BrowseResult,
)

__all__ = [
    # API Response Models
    "ArchivalInstitution",
    "HierarchyLevel",
    "Provenance",
    "Metadata",
    "PageInfo",
    "Snippet",
    "TranscribedText",
    "DocumentLinks",
    "SearchRecord",
    "RecordsResponse",
    # Search Results
    "SearchResult",
    # Browse Results
    "PageContext",
    "OAIPMHMetadata",
    "BrowseResult",
]

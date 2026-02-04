"""
RA-MCP Core: Core library for Riksarkivet MCP Server.

Provides models, configuration, API clients, formatters, and utilities
shared across all ra-mcp packages.
"""

__version__ = "0.2.7"

from .config import (
    SEARCH_API_BASE_URL,
    COLLECTION_API_BASE_URL,
    IIIF_MANIFEST_API_BASE_URL,
    OAI_BASE_URL,
    SOK_BASE_URL,
    ALTO_BASE_URL,
    BILDVISNING_BASE_URL,
    IIIF_IMAGE_BASE_URL,
    REQUEST_TIMEOUT,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MAX_DISPLAY,
    DEFAULT_MAX_PAGES,
    NAMESPACES,
    ALTO_NAMESPACES,
)

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
    # Search Results
    SearchResult,
    SearchSummary,
    # Browse Results
    PageContext,
    DocumentMetadata,
    BrowseResult,
)

__all__ = [
    # Config
    "SEARCH_API_BASE_URL",
    "COLLECTION_API_BASE_URL",
    "IIIF_MANIFEST_API_BASE_URL",
    "OAI_BASE_URL",
    "SOK_BASE_URL",
    "ALTO_BASE_URL",
    "BILDVISNING_BASE_URL",
    "IIIF_IMAGE_BASE_URL",
    "REQUEST_TIMEOUT",
    "DEFAULT_MAX_RESULTS",
    "DEFAULT_MAX_DISPLAY",
    "DEFAULT_MAX_PAGES",
    "NAMESPACES",
    "ALTO_NAMESPACES",
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
    # Search Results
    "SearchResult",
    "SearchSummary",
    # Browse Results
    "PageContext",
    "DocumentMetadata",
    "BrowseResult",
]

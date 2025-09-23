"""
Core module providing easy access to all ra-mcp functionality.
This module serves as a replacement for the monolithic ra_core.py.
"""

# Re-export all main classes and functions for backward compatibility
from .clients import SearchAPI, ALTOClient, OAIPMHClient, IIIFClient
from .services import PageContextService, SearchEnrichmentService, DisplayService
from .utils import HTTPClient, URLGenerator, parse_page_range
from .models import SearchHit, PageContext
from .config import (
    SEARCH_API_BASE_URL,
    COLLECTION_API_BASE_URL,
    IIIF_BASE_URL,
    OAI_BASE_URL,
    REQUEST_TIMEOUT,
    DEFAULT_MAX_RESULTS,
    DEFAULT_MAX_DISPLAY,
    DEFAULT_MAX_PAGES,
    NAMESPACES,
    ALTO_NAMESPACES
)

__all__ = [
    # Clients
    'SearchAPI',
    'ALTOClient',
    'OAIPMHClient',
    'IIIFClient',

    # Services
    'PageContextService',
    'SearchEnrichmentService',
    'DisplayService',

    # Utils
    'HTTPClient',
    'URLGenerator',
    'parse_page_range',

    # Models
    'SearchHit',
    'PageContext',

    # Config
    'SEARCH_API_BASE_URL',
    'COLLECTION_API_BASE_URL',
    'IIIF_BASE_URL',
    'OAI_BASE_URL',
    'REQUEST_TIMEOUT',
    'DEFAULT_MAX_RESULTS',
    'DEFAULT_MAX_DISPLAY',
    'DEFAULT_MAX_PAGES',
    'NAMESPACES',
    'ALTO_NAMESPACES'
]
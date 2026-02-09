"""
RA-MCP Browse: Browse domain for Riksarkivet document pages.

Provides clients, operations, and models for browsing document pages.
"""

__version__ = "0.3.0"

from .clients import ALTOClient, IIIFClient, OAIPMHClient
from .operations import BrowseOperations
from .models import BrowseResult, PageContext, OAIPMHMetadata

__all__ = [
    "ALTOClient",
    "IIIFClient",
    "OAIPMHClient",
    "BrowseOperations",
    "BrowseResult",
    "PageContext",
    "OAIPMHMetadata",
]

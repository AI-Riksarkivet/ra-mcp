"""
RA-MCP Browse: Browse domain for Riksarkivet document pages.

Provides clients, operations, and models for browsing document pages.
"""

__version__ = "0.3.0"

from .browse_operations import BrowseOperations
from .clients import ALTOClient, IIIFClient, OAIPMHClient
from .models import BrowseResult, OAIPMHMetadata, PageContext


__all__ = [
    "ALTOClient",
    "BrowseOperations",
    "BrowseResult",
    "IIIFClient",
    "OAIPMHClient",
    "OAIPMHMetadata",
    "PageContext",
]

"""
RA-MCP Browse: Browse domain for Riksarkivet document pages.

Provides clients and operations for browsing document pages.
Models are imported from ra_mcp_core.
"""

__version__ = "0.2.7"

from .clients import ALTOClient, IIIFClient, OAIPMHClient
from .operations import BrowseOperations

# Re-export models from core for convenience
from ra_mcp_core.models import BrowseResult, PageContext, OAIPMHMetadata, PageInfo

__all__ = [
    "ALTOClient",
    "IIIFClient",
    "OAIPMHClient",
    "BrowseOperations",
    "BrowseResult",
    "PageContext",
    "OAIPMHMetadata",
    "PageInfo",
]

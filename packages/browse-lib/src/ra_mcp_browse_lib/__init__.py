"""
RA-MCP Browse: Browse domain for Riksarkivet document pages.

Provides operations and models for browsing document pages.
Clients (ALTOClient, IIIFClient, OAIPMHClient) live in their own packages.
"""

__version__ = "0.3.0"

from ra_mcp_iiif_lib import IIIFClient
from ra_mcp_oai_pmh_lib import OAIPMHClient, OAIPMHMetadata
from ra_mcp_xml import ALTOClient

from .browse_operations import BrowseOperations
from .models import BrowseResult, PageContext


__all__ = [
    "ALTOClient",
    "BrowseOperations",
    "BrowseResult",
    "IIIFClient",
    "OAIPMHClient",
    "OAIPMHMetadata",
    "PageContext",
]

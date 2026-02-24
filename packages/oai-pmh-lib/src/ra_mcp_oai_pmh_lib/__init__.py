"""RA-MCP OAI-PMH: OAI-PMH client for Riksarkivet metadata."""

__version__ = "0.3.0"

from .client import OAIPMHClient
from .models import OAIPMHMetadata


__all__ = ["OAIPMHClient", "OAIPMHMetadata"]

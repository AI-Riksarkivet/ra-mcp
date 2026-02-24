"""RA-MCP IIIF: IIIF Collections client for Riksarkivet."""

__version__ = "0.3.0"

from .client import IIIFClient
from .models import IIIFCollection, IIIFManifest


__all__ = ["IIIFClient", "IIIFCollection", "IIIFManifest"]

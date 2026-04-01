"""RA-MCP IIIF: IIIF Collections client for Riksarkivet."""

__version__ = "0.3.0"

from .client import IIIFClient
from .models import IIIFCanvas, IIIFCollection, IIIFManifest, IIIFManifestDetail


__all__ = ["IIIFCanvas", "IIIFClient", "IIIFCollection", "IIIFManifest", "IIIFManifestDetail"]

"""Data models for IIIF collections and manifests."""

from pydantic import BaseModel


class IIIFManifest(BaseModel):
    """IIIF manifest reference."""

    id: str
    label: str | None = None


class IIIFCollection(BaseModel):
    """IIIF collection information."""

    id: str
    label: str | None = None
    manifests: list[IIIFManifest] = []

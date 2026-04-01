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


class IIIFCanvas(BaseModel):
    """A single canvas (page) from a IIIF manifest."""

    id: str
    label: str | None = None
    image_url: str = ""
    alto_url: str = ""


class IIIFManifestDetail(BaseModel):
    """Parsed IIIF manifest with canvas/image details."""

    id: str
    label: str | None = None
    canvases: list[IIIFCanvas] = []

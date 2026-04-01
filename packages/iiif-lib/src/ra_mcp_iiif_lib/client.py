"""
IIIF client for Riksarkivet.
"""

import logging

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_common.telemetry import get_tracer
from ra_mcp_iiif_lib.config import COLLECTION_API_BASE_URL
from ra_mcp_iiif_lib.models import IIIFCanvas, IIIFCollection, IIIFManifest, IIIFManifestDetail


logger = logging.getLogger("ra_mcp.iiif_client")

_tracer = get_tracer("ra_mcp.iiif_client")


class IIIFClient:
    """Client for IIIF collections and manifests."""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    async def get_collection(self, pid: str, timeout: int = 30) -> IIIFCollection | None:
        """Get IIIF collection with typed model.

        Args:
            pid: Persistent identifier for the collection.
            timeout: Request timeout in seconds.

        Returns:
            Parsed collection with manifests, or None on fetch failure.
        """
        with _tracer.start_as_current_span("IIIFClient.get_collection", attributes={"iiif.pid": pid}) as span:
            url = f"{COLLECTION_API_BASE_URL}/{pid}"
            data = await self._fetch_json(url, timeout)
            if not data:
                span.set_attribute("iiif.result", "not_found")
                return None

            manifests = self._parse_manifests(data.get("items", []))
            span.set_attribute("iiif.manifests_found", len(manifests))

            return IIIFCollection(
                id=data.get("id", pid),
                label=self._extract_iiif_label(data.get("label")),
                manifests=manifests,
            )

    def _parse_manifests(self, items: list[dict]) -> list[IIIFManifest]:
        """Parse Manifest items from a IIIF collection items list."""
        manifests: list[IIIFManifest] = []
        for item in items:
            if item.get("type") != "Manifest":
                continue
            url = item.get("id", "")
            manifests.append(
                IIIFManifest(
                    id=self._extract_manifest_identifier(url) or url,
                    label=self._extract_iiif_label(item.get("label")),
                )
            )
        return manifests

    async def fetch_manifest(self, manifest_url: str, timeout: int = 30) -> IIIFManifestDetail | None:
        """Fetch and parse a IIIF manifest, extracting canvas image URLs.

        Args:
            manifest_url: Full URL to the IIIF manifest JSON.
            timeout: Request timeout in seconds.

        Returns:
            Parsed manifest with canvases, or None on fetch failure.
        """
        with _tracer.start_as_current_span("IIIFClient.fetch_manifest", attributes={"iiif.manifest_url": manifest_url}) as span:
            data = await self._fetch_json(manifest_url, timeout)
            if not data:
                span.set_attribute("iiif.result", "not_found")
                return None

            canvases = self._parse_canvases(data.get("items", []))
            span.set_attribute("iiif.canvases_found", len(canvases))

            return IIIFManifestDetail(
                id=data.get("id", manifest_url),
                label=self._extract_iiif_label(data.get("label")),
                canvases=canvases,
            )

    def _parse_canvases(self, items: list[dict]) -> list[IIIFCanvas]:
        """Parse Canvas items from a IIIF manifest items list."""
        canvases: list[IIIFCanvas] = []
        for item in items:
            if item.get("type") != "Canvas":
                continue
            canvases.append(
                IIIFCanvas(
                    id=item.get("id", ""),
                    label=self._extract_iiif_label(item.get("label")),
                    image_url=self._extract_painting_image(item),
                    alto_url=self._extract_alto_url(item),
                )
            )
        return canvases

    @staticmethod
    def _extract_alto_url(canvas: dict) -> str:
        """Extract ALTO XML URL from a Canvas's seeAlso references.

        Checks type, format, and profile fields — different providers use
        different conventions (Riksarkivet: type="ALTO", Wellcome: profile contains "alto").
        """
        for ref in canvas.get("seeAlso", []):
            searchable = f"{ref.get('type', '')} {ref.get('format', '')} {ref.get('profile', '')}".lower()
            if "alto" in searchable:
                return ref.get("id", "")
        return ""

    def _extract_painting_image(self, canvas: dict) -> str:
        """Extract image URL from a Canvas's painting annotation."""
        for annotation_page in canvas.get("items", []):
            for annotation in annotation_page.get("items", []):
                if annotation.get("motivation") == "painting":
                    body = annotation.get("body", {})
                    return body.get("id", "")
        return ""

    def _extract_manifest_identifier(self, manifest_url: str) -> str:
        """Extract manifest identifier from URL.

        For ``https://…/arkis!R0001203/manifest`` returns ``arkis!R0001203``.
        For ``https://…/arkis/R0001203`` returns ``R0001203``.
        """
        if not manifest_url:
            return ""

        segments = manifest_url.rstrip("/").split("/")
        if "/manifest" in manifest_url and len(segments) >= 2:
            return segments[-2]
        return segments[-1] if segments else ""

    # -- IIIF label helpers --

    def _extract_iiif_label(self, label: str | dict | list | None, default: str = "Unknown") -> str:
        """Extract a display string from a IIIF label (language map, string, or None)."""
        if not label:
            return default
        if isinstance(label, str):
            return label
        if isinstance(label, dict):
            return self._label_from_language_map(label) or default
        return default

    def _label_from_language_map(self, language_map: dict) -> str | None:
        """Pick the best label from a IIIF language map (sv > en > none > first)."""
        for key in ("sv", "en", "none"):
            if key in language_map:
                return self._first_str(language_map[key])
        first_key = next(iter(language_map), None)
        if first_key is not None:
            return self._first_str(language_map[first_key])
        return None

    @staticmethod
    def _first_str(value: str | list) -> str:
        """Return the first string from a value that is either a string or a list."""
        if isinstance(value, list) and value:
            return str(value[0])
        return str(value)

    # -- HTTP --

    async def _fetch_json(self, url: str, timeout: int) -> dict | None:
        """Fetch JSON from a URL, returning None on failure."""
        try:
            return await self.http_client.get_json(url, timeout=timeout)
        except Exception as e:
            logger.warning("Failed to fetch IIIF collection from %s: %s", url, e)
            return None

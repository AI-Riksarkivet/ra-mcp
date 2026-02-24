"""
IIIF client for Riksarkivet.
"""

import logging

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_common.telemetry import get_tracer
from ra_mcp_iiif_lib.config import COLLECTION_API_BASE_URL
from ra_mcp_iiif_lib.models import IIIFCollection, IIIFManifest


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

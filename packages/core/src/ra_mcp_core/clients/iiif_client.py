"""
IIIF client for Riksarkivet.
"""

from typing import Dict, Optional, Union, List

from ..config import COLLECTION_API_BASE_URL
from ..utils.http_client import HTTPClient


class IIIFClient:
    """Client for IIIF collections and manifests."""

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    def explore_collection(self, pid: str, timeout: int = 30) -> Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """Explore IIIF collection to get manifests."""
        collection_endpoint_url = self._build_collection_url(pid)

        collection_response = self._fetch_collection_data(collection_endpoint_url, timeout)
        if not collection_response:
            return None

        collection_title = self._extract_collection_title(collection_response)
        available_manifests = self._extract_all_manifests(collection_response)

        return self._build_collection_result(collection_title, available_manifests, collection_endpoint_url)

    def _build_collection_url(self, persistent_identifier: str) -> str:
        """Build the collection API URL."""
        return f"{COLLECTION_API_BASE_URL}/{persistent_identifier}"

    def _fetch_collection_data(self, collection_url: str, timeout_seconds: int) -> Optional[Dict]:
        """Fetch collection data from IIIF endpoint using centralized HTTP client."""
        try:
            return self.http_client.get_json(collection_url, timeout=timeout_seconds)
        except Exception as e:
            # Log the error before returning None
            if hasattr(self.http_client, "logger") and self.http_client.logger:
                self.http_client.logger.error(f"Failed to fetch IIIF collection data from {collection_url}: {str(e)}")
            return None

    def _extract_collection_title(self, collection_data: Dict) -> str:
        """Extract title from collection data."""
        collection_label = collection_data.get("label", {})
        return self._extract_iiif_label(collection_label, "Unknown Collection")

    def _extract_all_manifests(self, collection_data: Dict) -> List[Dict[str, str]]:
        """Extract all manifests from collection items."""
        extracted_manifests = []
        collection_items = collection_data.get("items", [])

        for item in collection_items:
            if self._is_manifest_item(item):
                manifest_info = self._process_manifest_item(item)
                extracted_manifests.append(manifest_info)

        return extracted_manifests

    def _is_manifest_item(self, item: Dict) -> bool:
        """Check if an item is a manifest."""
        return item.get("type") == "Manifest"

    def _process_manifest_item(self, manifest_item: Dict) -> Dict[str, str]:
        """Process a single manifest item into structured data."""
        manifest_label = self._extract_manifest_label(manifest_item)
        manifest_endpoint_url = manifest_item.get("id", "")
        manifest_identifier = self._extract_manifest_identifier(manifest_endpoint_url)

        return {
            "id": manifest_identifier or manifest_endpoint_url,
            "label": manifest_label,
            "url": manifest_endpoint_url,
        }

    def _extract_manifest_label(self, manifest_item: Dict) -> str:
        """Extract label from manifest item."""
        item_label = manifest_item.get("label", {})
        return self._extract_iiif_label(item_label, "Untitled")

    def _extract_manifest_identifier(self, manifest_url: str) -> str:
        """Extract manifest identifier from URL."""
        if not manifest_url:
            return ""

        url_without_trailing_slash = manifest_url.rstrip("/")
        url_segments = url_without_trailing_slash.split("/")

        if "/manifest" in manifest_url and len(url_segments) >= 2:
            return url_segments[-2]

        return url_segments[-1] if url_segments else ""

    def _build_collection_result(self, title: str, manifests: List[Dict[str, str]], collection_url: str) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        """Build the final collection result structure."""
        return {
            "title": title,
            "manifests": manifests,
            "collection_url": collection_url,
        }

    def _extract_iiif_label(self, label_object: Union[str, Dict, List], default_value: str = "Unknown") -> str:
        """Smart IIIF label extraction supporting all language map formats."""
        if not label_object:
            return default_value

        if isinstance(label_object, str):
            return label_object

        if isinstance(label_object, dict):
            extracted_label = self._extract_label_from_language_map(label_object)
            if extracted_label:
                return extracted_label

        return str(label_object) if label_object else default_value

    def _extract_label_from_language_map(self, language_map: Dict) -> Optional[str]:
        """Extract label from IIIF language map."""
        preferred_languages = ["sv", "en", "none"]

        for language_code in preferred_languages:
            if language_code in language_map:
                language_value = language_map[language_code]
                return self._extract_value_from_language_entry(language_value)

        first_available_language = next(iter(language_map.keys()), None)
        if first_available_language:
            language_value = language_map[first_available_language]
            return self._extract_value_from_language_entry(language_value)

        return None

    def _extract_value_from_language_entry(self, language_entry: Union[str, List]) -> str:
        """Extract string value from language entry."""
        if isinstance(language_entry, list) and language_entry:
            return str(language_entry[0])
        return str(language_entry)

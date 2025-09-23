"""
IIIF client for Riksarkivet.
"""

from typing import Dict, Optional, Union, List

from ..config import COLLECTION_API_BASE_URL
from ..utils import HTTPClient


class IIIFClient:
    """Client for IIIF collections and manifests."""

    def __init__(self):
        self.session = HTTPClient.create_session()

    def explore_collection(
        self, pid: str, timeout: int = 10
    ) -> Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """Explore IIIF collection to get manifests."""
        collection_url = f"{COLLECTION_API_BASE_URL}/{pid}"

        try:
            response = self.session.get(collection_url, timeout=timeout)
            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            title = self._extract_iiif_label(
                data.get("label", {}), "Unknown Collection"
            )

            manifests = []
            for item in data.get("items", []):
                if item.get("type") == "Manifest":
                    manifest_title = self._extract_iiif_label(
                        item.get("label", {}), "Untitled"
                    )
                    manifest_url = item.get("id", "")
                    manifest_id = (
                        manifest_url.rstrip("/").split("/")[-2]
                        if "/manifest" in manifest_url
                        else manifest_url.split("/")[-1]
                    )

                    manifests.append(
                        {
                            "id": manifest_id or manifest_url,
                            "label": manifest_title,
                            "url": manifest_url,
                        }
                    )

            return {
                "title": title,
                "manifests": manifests,
                "collection_url": collection_url,
            }

        except Exception:
            return None

    @staticmethod
    def _extract_iiif_label(
        label_obj: Union[str, Dict, List], default: str = "Unknown"
    ) -> str:
        """Smart IIIF label extraction supporting all language map formats."""
        if not label_obj:
            return default

        if isinstance(label_obj, str):
            return label_obj

        if isinstance(label_obj, dict):
            for lang in ["sv", "en", "none"]:
                if lang in label_obj:
                    value = label_obj[lang]
                    return value[0] if isinstance(value, list) and value else str(value)

            first_lang = next(iter(label_obj.keys()), None)
            if first_lang:
                value = label_obj[first_lang]
                return value[0] if isinstance(value, list) and value else str(value)

        return str(label_obj) if label_obj else default

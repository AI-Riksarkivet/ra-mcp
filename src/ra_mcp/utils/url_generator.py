"""
URL generation utilities for Riksarkivet resources.
"""

import urllib.parse
from typing import Optional

from ..config import COLLECTION_API_BASE_URL, IIIF_BASE_URL


class URLGenerator:
    """Generate various URLs for Riksarkivet resources."""

    @staticmethod
    def clean_id(pid: str) -> str:
        """Extract clean ID from PID."""
        return pid[6:] if pid.startswith('arkis!') else pid

    @staticmethod
    def format_page_number(page_number: str) -> str:
        """Format page number with proper padding."""
        clean_page = page_number.lstrip('_')
        if clean_page.isdigit():
            return f"{int(clean_page):05d}"
        return clean_page.zfill(5)

    @classmethod
    def alto_url(cls, pid: str, page_number: str) -> Optional[str]:
        """Generate ALTO URL from PID and page number."""
        try:
            manifest_id = cls.clean_id(pid)
            padded_page = cls.format_page_number(page_number)

            if len(manifest_id) >= 4:
                first_4_chars = manifest_id[:4]
                return f"https://sok.riksarkivet.se/dokument/alto/{first_4_chars}/{manifest_id}/{manifest_id}_{padded_page}.xml"
            return None
        except Exception:
            return None

    @classmethod
    def iiif_image_url(cls, pid: str, page_number: str) -> Optional[str]:
        """Generate IIIF image URL from PID and page number."""
        try:
            clean_id = cls.clean_id(pid)
            padded_page = cls.format_page_number(page_number)
            return f"https://lbiiif.riksarkivet.se/arkis!{clean_id}_{padded_page}/full/max/0/default.jpg"
        except Exception:
            return None

    @classmethod
    def bildvisning_url(cls, pid: str, page_number: str, search_term: Optional[str] = None) -> Optional[str]:
        """Generate bildvisning URL with optional search highlighting."""
        try:
            clean_id = cls.clean_id(pid)
            padded_page = cls.format_page_number(page_number)
            base_url = f"https://sok.riksarkivet.se/bildvisning/{clean_id}_{padded_page}"

            if search_term and search_term.strip():
                encoded_term = urllib.parse.quote(search_term.strip())
                return f"{base_url}#?q={encoded_term}"
            return base_url
        except Exception:
            return None

    @classmethod
    def collection_url(cls, pid: str) -> Optional[str]:
        """Generate IIIF collection URL from PID."""
        try:
            clean_id = cls.clean_id(pid)
            return f"{COLLECTION_API_BASE_URL}/{clean_id}"
        except Exception:
            return None

    @classmethod
    def manifest_url(cls, pid: str, manifest_id: Optional[str] = None) -> Optional[str]:
        """Generate IIIF manifest URL from PID and optional manifest ID."""
        try:
            clean_id = cls.clean_id(pid)
            if manifest_id:
                return f"{IIIF_BASE_URL}/{manifest_id}/manifest"
            return f"{IIIF_BASE_URL}/{clean_id}_001/manifest"
        except Exception:
            return None
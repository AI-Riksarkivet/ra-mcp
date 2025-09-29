"""
URL generation utilities for Riksarkivet resources.
"""

import urllib.parse
from typing import Optional

from ..config import (
    ALTO_BASE_URL,
    BILDVISNING_BASE_URL,
    IIIF_IMAGE_BASE_URL,
)


def remove_arkis_prefix(manifest_id: str) -> str:
    """Remove arkis! prefix from manifest ID if present.

    Args:
        manifest_id: Manifest ID string, potentially with arkis! prefix

    Returns:
        Manifest ID without arkis! prefix
    """

    return manifest_id[6:] if manifest_id.startswith("arkis!") else manifest_id


def format_page_number(page_number: str) -> str:
    """Format page number with proper padding.

    Args:
        page_number: Page number string

    Returns:
        Padded page number (5 digits)
    """
    clean_page = page_number.lstrip("_")
    if clean_page.isdigit():
        return f"{int(clean_page):05d}"
    return clean_page.zfill(5)


def alto_url(manifest_id: str, page_number: str) -> Optional[str]:
    """Generate ALTO URL from manifest ID and page number.

    Args:
        manifest_id: Manifest identifier (not PID - should be clean manifest ID)
        page_number: Page number

    Returns:
        ALTO XML URL or None if cannot generate
    """
    try:
        padded_page = format_page_number(page_number)

        if len(manifest_id) >= 4:
            first_4_chars = manifest_id[:4]
            return f"{ALTO_BASE_URL}/{first_4_chars}/{manifest_id}/{manifest_id}_{padded_page}.xml"
        return None
    except Exception:
        return None


def iiif_image_url(manifest_id: str, page_number: str) -> Optional[str]:
    """Generate IIIF image URL from manifest ID and page number.

    Args:
        manifest_id: Manifest ID
        page_number: Page number

    Returns:
        IIIF image URL or None if cannot generate
    """
    try:
        clean_manifest_id = remove_arkis_prefix(manifest_id)
        padded_page = format_page_number(page_number)
        return f"{IIIF_IMAGE_BASE_URL}!{clean_manifest_id}_{padded_page}/full/max/0/default.jpg"
    except Exception:
        return None


def bildvisning_url(
    manifest_id: str, page_number: str, search_term: Optional[str] = None
) -> Optional[str]:
    """Generate bildvisning URL with optional search highlighting.

    Args:
        manifest_id: Manifest ID
        page_number: Page number
        search_term: Optional search term to highlight

    Returns:
        Bildvisning URL or None if cannot generate
    """
    try:
        clean_manifest_id = remove_arkis_prefix(manifest_id)
        padded_page = format_page_number(page_number)
        base_url = f"{BILDVISNING_BASE_URL}/{clean_manifest_id}_{padded_page}"

        if search_term and search_term.strip():
            encoded_term = urllib.parse.quote(search_term.strip())
            return f"{base_url}#?q={encoded_term}"
        return base_url
    except Exception:
        return None

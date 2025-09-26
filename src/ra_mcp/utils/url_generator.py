"""
URL generation utilities for Riksarkivet resources.
"""

import urllib.parse
from typing import Optional

from ..config import IIIF_COLLECTION_API_BASE_URL, IIIF_MANIFEST_API_BASE_URL


def prepare_manifest_id_for_alto(manifest_id: str) -> str:
    """Prepare manifest ID for ALTO URL generation by removing arkis! prefix.

    Args:
        manifest_id: Manifest/batch ID (NOT a PID), potentially with arkis! prefix

    Returns:
        Clean manifest ID without arkis! prefix for ALTO URL construction
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
            return f"https://sok.riksarkivet.se/dokument/alto/{first_4_chars}/{manifest_id}/{manifest_id}_{padded_page}.xml"
        return None
    except Exception:
        return None


def iiif_image_url(pid: str, page_number: str) -> Optional[str]:
    """Generate IIIF image URL from PID and page number.

    Args:
        pid: Document PID
        page_number: Page number

    Returns:
        IIIF image URL or None if cannot generate
    """
    try:
        # For image URLs, use PID directly with arkis! prefix
        padded_page = format_page_number(page_number)
        return f"{IIIF_MANIFEST_API_BASE_URL}{pid}_{padded_page}/full/max/0/default.jpg"
    except Exception:
        return None


def bildvisning_url(
    pid: str, page_number: str, search_term: Optional[str] = None
) -> Optional[str]:
    """Generate bildvisning URL with optional search highlighting.

    Args:
        pid: Document PID
        page_number: Page number
        search_term: Optional search term to highlight

    Returns:
        Bildvisning URL or None if cannot generate
    """
    try:
        # Bildvisning URLs use clean PID without arkis! prefix
        padded_page = format_page_number(page_number)
        base_url = f"https://sok.riksarkivet.se/bildvisning/{pid}_{padded_page}"

        if search_term and search_term.strip():
            encoded_term = urllib.parse.quote(search_term.strip())
            return f"{base_url}#?q={encoded_term}"
        return base_url
    except Exception:
        return None


def collection_url(pid: str) -> Optional[str]:
    """Generate IIIF collection URL from PID.

    Args:
        pid: Document PID

    Returns:
        IIIF collection URL or None if cannot generate
    """
    try:
        # Collection URLs use PID directly without modification
        return f"{IIIF_COLLECTION_API_BASE_URL}/{pid}"
    except Exception:
        return None


def manifest_url(pid: str, manifest_id: Optional[str] = None) -> Optional[str]:
    """Generate IIIF manifest URL from PID and optional manifest ID.

    Args:
        pid: Document PID
        manifest_id: Optional specific manifest ID

    Returns:
        IIIF manifest URL or None if cannot generate
    """
    try:
        if manifest_id:
            # If manifest_id is provided, use it with arkis! prefix
            clean_manifest = prepare_manifest_id_for_alto(manifest_id)
            return f"{IIIF_MANIFEST_API_BASE_URL}{clean_manifest}/manifest"
        # Default: derive manifest from PID by adding _001
        return f"{IIIF_MANIFEST_API_BASE_URL}{pid}_001/manifest"
    except Exception:
        return None

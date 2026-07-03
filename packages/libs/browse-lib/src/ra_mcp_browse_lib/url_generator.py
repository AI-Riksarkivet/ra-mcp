"""
URL generation utilities for Riksarkivet resources.
"""

import logging
import re
import urllib.parse

from .config import ALTO_BASE_URL, BILDVISNING_BASE_URL, IIIF_IMAGE_BASE_URL


logger = logging.getLogger("ra_mcp.url_generator")

# IIIF Image API URL: {server}/{identifier}/{region}/{size}/{rotation}/{quality}.{fmt}
# This captures the {size} segment (after /full/) so it can be re-bounded.
_IIIF_SIZE_RE = re.compile(r"(/full/)[^/]+(/[^/]+/[^/]+)$")


def iiif_resize(image_url: str, size: str) -> str:
    """Re-bound an existing IIIF Image URL to a new ``size`` segment.

    Swaps the IIIF Image API size component (e.g. ``max`` in
    ``/full/max/0/default.jpg``) for ``size`` — ``"1500,"`` for a 1500px-wide
    page render, ``"150,"`` for a thumbnail (IIIF Image API 3.0 ``w,`` syntax).
    Delivering size-bounded images by direct URL (browser-fetched, CSP-allowed)
    is the MCP Apps sanctioned path; it avoids downloading full-resolution scans
    server-side and base64-encoding them through the tool-result channel.

    Returns the URL unchanged if it is not a recognisable IIIF Image URL, so
    non-IIIF sources pass through untouched.
    """
    return _IIIF_SIZE_RE.sub(rf"\g<1>{size}\g<2>", image_url, count=1)


def remove_arkis_prefix(manifest_id: str) -> str:
    """Remove arkis! prefix from manifest ID if present.

    Args:
        manifest_id: Manifest ID string, potentially with arkis! prefix

    Returns:
        Manifest ID without arkis! prefix
    """

    return manifest_id.removeprefix("arkis!")


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


def alto_url(manifest_id: str, page_number: str) -> str | None:
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
    except Exception as e:
        logger.warning("Failed to generate ALTO URL for manifest=%s page=%s: %s", manifest_id, page_number, e)
        return None


def iiif_image_url(manifest_id: str, page_number: str) -> str | None:
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
    except Exception as e:
        logger.warning("Failed to generate IIIF image URL for manifest=%s page=%s: %s", manifest_id, page_number, e)
        return None


def bildvisning_url(manifest_id: str, page_number: str, search_term: str | None = None) -> str | None:
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
    except Exception as e:
        logger.warning("Failed to generate bildvisning URL for manifest=%s page=%s: %s", manifest_id, page_number, e)
        return None

"""Document resolution — bridge between browse domain and viewer tools."""

from ra_mcp_browse_lib.browse_operations import BrowseOperations
from ra_mcp_common.http_client import HTTPClient, default_http_client
from ra_mcp_viewer_mcp.models import ResolvedDocument


async def browse_resolve_document(
    reference_code: str,
    pages: str,
    highlight_term: str | None,
    max_pages: int,
    *,
    http_client: HTTPClient = default_http_client,
) -> ResolvedDocument:
    """Resolve reference code → ResolvedDocument.

    Raises ValueError for bad input, LookupError for no results.
    """
    if not reference_code.strip():
        raise ValueError("reference_code must not be empty.")
    if not pages.strip():
        raise ValueError("pages must not be empty.")

    browse_ops = BrowseOperations(http_client=http_client)
    result = await browse_ops.browse_document(
        reference_code=reference_code,
        pages=pages,
        highlight_term=highlight_term,
        max_pages=max_pages,
    )

    if not result.contexts:
        raise LookupError(f"No pages found for {reference_code} pages={pages}.")

    first = result.contexts[0]
    return ResolvedDocument(
        image_urls=[c.image_url for c in result.contexts],
        text_layer_urls=[c.alto_url for c in result.contexts],
        page_numbers=[c.page_number for c in result.contexts],
        first_transcription=first.full_text.strip() if first.full_text else "",
    )


def validate_url_pairs(
    image_urls: list[str],
    text_layer_urls: list[str],
    metadata: list[str] | None = None,
) -> str | None:
    """Return error message if URL lists are invalid, else None."""
    if not image_urls:
        return "image_urls must not be empty."
    if len(image_urls) != len(text_layer_urls):
        return f"Mismatched URL counts ({len(image_urls)} images vs {len(text_layer_urls)} text layers)."
    if metadata and len(metadata) != len(image_urls):
        return f"metadata length ({len(metadata)}) must match image_urls length ({len(image_urls)})."
    return None

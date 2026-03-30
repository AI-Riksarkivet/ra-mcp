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

    return ResolvedDocument(
        image_urls=[c.image_url for c in result.contexts],
        text_layer_urls=[c.alto_url for c in result.contexts],
        page_numbers=[c.page_number for c in result.contexts],
        bildvisning_urls=[c.bildvisning_url for c in result.contexts],
        document_info=_format_oai_metadata(result.oai_metadata, reference_code),
    )


def _format_oai_metadata(oai_metadata: object | None, reference_code: str) -> str:
    """Format OAI-PMH metadata as markdown for the info panel."""
    lines = [f"**Reference code:** {reference_code}"]
    if oai_metadata is None:
        return "\n\n".join(lines)

    oai = oai_metadata
    if title := getattr(oai, "title", None):
        lines.insert(0, f"## {title}")
    if unitdate := getattr(oai, "unitdate", None):
        lines.append(f"**Date:** {unitdate}")
    if repository := getattr(oai, "repository", None):
        lines.append(f"**Repository:** {repository}")
    if unitid := getattr(oai, "unitid", None):
        lines.append(f"**Unit ID:** {unitid}")
    if description := getattr(oai, "description", None):
        lines.append(f"\n{description}")

    return "\n\n".join(lines)


def validate_url_pairs(
    image_urls: list[str],
    text_layer_urls: list[str],
) -> str | None:
    """Return error message if URL lists are invalid, else None."""
    if not image_urls:
        return "image_urls must not be empty."
    if len(image_urls) != len(text_layer_urls):
        return f"Mismatched URL counts ({len(image_urls)} images vs {len(text_layer_urls)} text layers)."
    return None

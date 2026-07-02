"""Document resolution — bridge between browse domain and viewer tools."""

from ra_mcp_browse_lib import url_generator
from ra_mcp_browse_lib.browse_operations import BrowseOperations
from ra_mcp_common.http_client import HTTPClient, default_http_client
from ra_mcp_iiif_lib import IIIFClient
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


async def manifest_resolve_document(
    manifest_url: str,
    max_pages: int,
    *,
    http_client: HTTPClient = default_http_client,
) -> ResolvedDocument:
    """Resolve a IIIF manifest URL → ResolvedDocument with image URLs.

    Raises ValueError for bad input, LookupError for no results.
    """
    if not manifest_url.strip():
        raise ValueError("manifest_url must not be empty.")

    iiif_client = IIIFClient(http_client=http_client)
    manifest = await iiif_client.fetch_manifest(manifest_url)

    if not manifest or not manifest.canvases:
        raise LookupError(f"No pages found in manifest: {manifest_url}")

    canvases = manifest.canvases[:max_pages]

    return ResolvedDocument(
        image_urls=[c.image_url for c in canvases],
        text_layer_urls=[c.alto_url for c in canvases],
        page_numbers=list(range(1, len(canvases) + 1)),
        bildvisning_urls=[""] * len(canvases),
        document_info=f"**Document:** {manifest.label or 'Unknown'}\n\n**Manifest:** {manifest_url}",
    )


def _parse_bild_id(bild_id: str) -> tuple[str, str]:
    """Split a bild_id into (manifest_id, page_number).

    A bild_id like 'C0056829_00001' splits at the last '_' into
    manifest_id='C0056829' and page_number='00001'.

    Raises ValueError if the format is invalid.
    """
    idx = bild_id.rfind("_")
    if idx <= 0:
        raise ValueError(f"Invalid bild_id format: {bild_id!r} (expected e.g. 'C0056829_00001').")
    return bild_id[:idx], bild_id[idx + 1 :]


def bild_resolve_document(
    bild_ids: list[str],
    highlight_term: str | None = None,
) -> ResolvedDocument:
    """Resolve one or more bild_ids to a ResolvedDocument.

    Each bild_id (e.g. 'C0056829_00001') is split into manifest_id + page_number,
    then URLs are generated using the existing url_generator.

    Raises ValueError if any bild_id is invalid.
    """
    if not bild_ids:
        raise ValueError("bild_ids must not be empty.")

    image_urls: list[str] = []
    text_layer_urls: list[str] = []
    page_numbers: list[int] = []
    bildvisning_urls: list[str] = []

    for bild_id in bild_ids:
        manifest_id, page_num = _parse_bild_id(bild_id.strip())

        image_url = url_generator.iiif_image_url(manifest_id, page_num)
        alto = url_generator.alto_url(manifest_id, page_num)
        bv = url_generator.bildvisning_url(manifest_id, page_num, highlight_term)

        image_urls.append(image_url or "")
        text_layer_urls.append(alto or "")
        page_numbers.append(int(page_num) if page_num.lstrip("0").isdigit() or page_num == "0" * len(page_num) else 0)
        bildvisning_urls.append(bv or "")

    return ResolvedDocument(
        image_urls=image_urls,
        text_layer_urls=text_layer_urls,
        page_numbers=page_numbers,
        bildvisning_urls=bildvisning_urls,
        document_info=f"**Bild ID:** {', '.join(bild_ids)}",
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

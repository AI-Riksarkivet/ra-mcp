"""
Browse MCP tool for Riksarkivet document pages.

Provides the browse_document tool for viewing full page transcriptions.
"""

import logging

from fastmcp import Context

from ra_mcp_browse.models import BrowseResult
from ra_mcp_browse.operations import BrowseOperations
from ra_mcp_common.utils.formatting import format_error_message
from ra_mcp_common.utils.http_client import default_http_client

from .formatter import PlainTextFormatter


logger = logging.getLogger(__name__)


def register_browse_tool(mcp) -> None:
    """Register the browse tool with the MCP server."""

    @mcp.tool(
        name="document",
        version="1.0",
        timeout=60.0,
        tags={"browse"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description="""Browse specific pages of a document by reference code and view full transcriptions.

    This tool retrieves complete page transcriptions from historical documents in Swedish.
    Each result includes the full transcribed text as it appears in the original document,
    plus direct links to view the original page images in Riksarkivet's image viewer (bildvisaren).
    Prefer showing the whole transcription and link in responses of individual pages.
    Download some of the nearby pages too on selected pages if context seem to be missing from the transcript
    to get a better picture.

    Original text:
    transcript

    Translation:
    Modern translation in language of user

    Links

    IMPORTANT BEHAVIORS:
    - **Blank pages**: Pages may show "(Empty page - no transcribed text)" if the ALTO file exists
      but contains no text (cover pages, blank pages, etc.). These are still digitised materials.
    - **Non-digitised materials**: If no ALTO files exist (404 errors), the tool returns metadata only
      including title, date range, description, and links to view the material online.
    - **Mixed content**: Documents may have blank cover pages followed by pages with text content.

    Key features:
    - Returns full page transcriptions in original language (usually Swedish)
    - Shows "(Empty page - no transcribed text)" for blank pages that are digitised but have no text
    - Provides metadata (title, date, description) for non-digitised materials
    - Provides links to bildvisaren (Riksarkivet's image viewer) for viewing original documents
    - Supports single pages, page ranges, or multiple specific pages
    - Direct links to ALTO XML for detailed text layout information
    - IIIF manifest and image URLs when available

    Parameters:
    - reference_code: Document reference code from search results (e.g., "SE/RA/420422/01")
    - pages: Page specification - single ("5"), range ("1-10"), or comma-separated ("5,7,9")
    - highlight_term: Optional keyword to highlight in the transcription
    - max_pages: Maximum number of pages to retrieve (default: 20)
    - dedup: Session deduplication (default: True). When True, pages already shown in this session are replaced with a one-liner stub. Set to False to force full transcriptions.
    - research_context: Brief summary of the user's research goal and why they are browsing this document. Infer this from the conversation. If the user's intent is unclear, ASK them what they are researching and what kind of information they need before browsing. Examples: "Examining witchcraft trial testimony mentioned in search results", "Reading full court protocol to understand a legal dispute from the 1790s". This is used for telemetry and logging only — it does not affect results.

    IMPORTANT - Avoid redundant calls:
    - This tool remembers which pages it has shown you in this session. Re-browsing the same pages returns stubs instead of full text.
    - If you already have page transcriptions in your conversation context, reference that data directly instead of calling this tool again.
    - Only call again when you need pages you haven't seen yet, or set dedup=False if you truly need the full text again.

    Examples:
    - browse_document("SE/RA/420422/01", "5") - View full transcription of page 5
    - browse_document("SE/RA/420422/01", "1-10") - View pages 1 through 10
    - browse_document("SE/RA/420422/01", "5,7,9", highlight_term="Stockholm") - View specific pages with highlighting

    Note: Transcriptions are as they appear in the historical documents.
    Use this tool when you need complete page content rather than just search snippets.
    """,
    )
    async def browse_document(
        reference_code: str,
        pages: str,
        highlight_term: str | None = None,
        max_pages: int = 20,
        dedup: bool = True,
        research_context: str | None = None,
        ctx: Context | None = None,
    ) -> str:
        """
        Browse specific pages of a document by reference code.

        Returns:
        - Full transcribed text for each requested page
        - Optional keyword highlighting
        - Direct links to images and ALTO XML

        Examples:
        - browse_document("SE/RA/420422/01", "5") - View page 5
        - browse_document("SE/RA/420422/01", "1-10") - View pages 1 through 10
        - browse_document("SE/RA/420422/01", "5,7,9", highlight_term="Stockholm") - View specific pages with highlighting
        """
        # Input validation
        if not reference_code or not reference_code.strip():
            return format_error_message("reference_code must not be empty", error_suggestions=["Provide a document reference code, e.g. 'SE/RA/420422/01'"])
        if not pages or not pages.strip():
            return format_error_message("pages must not be empty", error_suggestions=["Specify pages like '1-5', '1,3,5', or '7'"])

        if research_context:
            logger.info(f"MCP Tool: browse_document | context: {research_context}")

        try:
            browse_operations = BrowseOperations(http_client=default_http_client)
            formatter = PlainTextFormatter()

            browse_result = _fetch_document_pages(
                browse_operations,
                reference_code=reference_code,
                pages=pages,
                highlight_term=highlight_term,
                max_pages=max_pages,
            )

            # Load session state for dedup
            seen_page_numbers: set[int] | None = None
            if dedup and ctx is not None:
                seen_browse: dict[str, list[int]] = await ctx.get_state("seen_browse") or {}
                seen_page_numbers = set(seen_browse.get(reference_code, []))
                logger.info(
                    "[browse] Dedup state loaded: %d documents tracked, %d pages previously seen for %s",
                    len(seen_browse),
                    len(seen_page_numbers),
                    reference_code,
                )

            if not browse_result.contexts:
                # Check if we have metadata to display for non-digitised materials
                if browse_result.oai_metadata:
                    return formatter.format_browse_results(browse_result, highlight_term, seen_page_numbers=seen_page_numbers)
                return _generate_no_pages_found_message(reference_code)

            result = formatter.format_browse_results(browse_result, highlight_term, seen_page_numbers=seen_page_numbers)

            # Update session state with newly shown pages
            if dedup and ctx is not None:
                all_pages = set(seen_browse.get(reference_code, []))
                for context in browse_result.contexts:
                    all_pages.add(context.page_number)
                seen_browse[reference_code] = sorted(all_pages)
                await ctx.set_state("seen_browse", seen_browse)
                logger.info("[browse] Dedup state saved: %s now has %d pages tracked", reference_code, len(all_pages))

            return result

        except Exception as e:
            logger.error("MCP browse_document failed: %s: %s", type(e).__name__, e, exc_info=True)
            return format_error_message(
                f"Browse failed: {e!s}",
                error_suggestions=[
                    "Check the reference code format",
                    "Verify page numbers are valid",
                    "Try with fewer pages",
                ],
            )


def _fetch_document_pages(browse_operations, **browse_params) -> BrowseResult:
    """Fetch document pages with the given parameters."""
    return browse_operations.browse_document(**browse_params)


def _generate_no_pages_found_message(reference_code) -> str:
    """Generate error message when no pages are found."""
    return format_error_message(
        f"Could not load pages for {reference_code}",
        error_suggestions=[
            "The pages might not have transcriptions",
            "Try different page numbers",
            "Check if the document is fully digitized",
        ],
    )

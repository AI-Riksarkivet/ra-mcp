"""
Browse MCP tool for Riksarkivet document pages.

Provides the browse_document tool for viewing full page transcriptions.
"""

import logging
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from ra_mcp_browse.browse_operations import BrowseOperations
from ra_mcp_browse.models import BrowseResult
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
        description=(
            "View full page transcriptions of a document by reference code. Use reference codes from search results. "
            "Returns original text (usually Swedish), links to bildvisaren (image viewer), and ALTO XML.\n"
            "Blank pages are normal (digitised but no text). Non-digitised materials return metadata only. "
            "Session dedup: re-browsing same pages returns stubs. Set dedup=False to force full text."
        ),
    )
    async def browse_document(
        reference_code: Annotated[str, Field(description="Document reference code from search results (e.g. 'SE/RA/420422/01').")],
        pages: Annotated[str, Field(description="Page specification: single ('5'), range ('1-10'), or comma-separated ('5,7,9').")],
        highlight_term: Annotated[str | None, Field(description="Optional keyword to highlight in the transcription.")] = None,
        max_pages: Annotated[int, Field(description="Maximum pages to retrieve.")] = 20,
        dedup: Annotated[bool, Field(description="Session deduplication. True replaces already-shown pages with stubs; False forces full text.")] = True,
        research_context: Annotated[str | None, Field(description="Brief summary of the user's research goal. Used for telemetry only.")] = None,
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
            logger.info("MCP Tool: browse_document | context: %s", research_context)

        try:
            browse_operations = BrowseOperations(http_client=default_http_client)
            formatter = PlainTextFormatter()

            session_id = ctx.session_id if ctx is not None else None
            browse_result = _fetch_document_pages(
                browse_operations,
                reference_code=reference_code,
                pages=pages,
                highlight_term=highlight_term,
                max_pages=max_pages,
                research_context=research_context,
                session_id=session_id,
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

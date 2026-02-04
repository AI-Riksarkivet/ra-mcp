"""
Browse MCP tool for Riksarkivet document pages.

Provides the browse_document tool for viewing full page transcriptions.
"""

from typing import Optional

from ra_mcp_core.formatters import format_error_message
from ra_mcp_core.utils.http_client import default_http_client
from ra_mcp_search.formatters import PlainTextFormatter
from ra_mcp_search.operations import BrowseOperations


def register_browse_tool(mcp) -> None:
    """Register the browse tool with the MCP server."""

    @mcp.tool(
        name="browse_document",
        description="""Browse specific pages of a document by reference code and view full transcriptions.

    This tool retrieves complete page transcriptions from historical documents in Swedish.
    Each result includes the full transcribed text as it appears in the original document,
    plus direct links to view the original page images in Riksarkivet's image viewer (bildvisaren).
    Prefer showing the whole transcription and link in responses of individual pages.
    Download some of the nearby pages too on selected pages if context seem to be missing from the trancript
    to get a better picture

    Original text:
    transcript

    Translation
    Modern translation in language of user

    Links

    Key features:
    - Returns full page transcriptions in (original language)
    - Provides links to bildvisaren (Riksarkivet's image viewer) for viewing original documents
    - Supports single pages, page ranges, or multiple specific pages
    - Direct links to ALTO XML for detailed text layout information

    Parameters:
    - reference_code: Document reference code from search results (e.g., "SE/RA/420422/01")
    - pages: Page specification - single ("5"), range ("1-10"), or comma-separated ("5,7,9")
    - highlight_term: Optional keyword to highlight in the transcription
    - max_pages: Maximum number of pages to retrieve (default: 20)

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
        highlight_term: Optional[str] = None,
        max_pages: int = 20,
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

            if not browse_result.contexts:
                return _generate_no_pages_found_message(reference_code)

            result = formatter.format_browse_results(browse_result, highlight_term)
            # PlainTextFormatter always returns string
            return result

        except Exception as e:
            return format_error_message(
                f"Browse failed: {str(e)}",
                error_suggestions=[
                    "Check the reference code format",
                    "Verify page numbers are valid",
                    "Try with fewer pages",
                ],
            )


def _fetch_document_pages(browse_operations, **browse_params):
    """Fetch document pages with the given parameters."""
    return browse_operations.browse_document(**browse_params)


def _generate_no_pages_found_message(reference_code):
    """Generate error message when no pages are found."""
    return format_error_message(
        f"Could not load pages for {reference_code}",
        error_suggestions=[
            "The pages might not have transcriptions",
            "Try different page numbers",
            "Check if the document is fully digitized",
        ],
    )

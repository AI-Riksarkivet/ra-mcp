"""
Thin facade over SearchOperations and BrowseOperations for TUI use.

All methods are synchronous (called from Textual workers via @work(thread=True)).
"""

from ra_mcp_browse.models import BrowseResult
from ra_mcp_browse.operations import BrowseOperations
from ra_mcp_common.utils.http_client import HTTPClient
from ra_mcp_search.models import SearchResult
from ra_mcp_search.operations import SearchOperations


class ArchiveService:
    """Unified access to search and browse operations.

    Holds a single shared HTTPClient and creates operations instances once.
    """

    def __init__(self) -> None:
        self._http = HTTPClient()
        self._search = SearchOperations(self._http)
        self._browse = BrowseOperations(self._http)

    def search_transcribed(
        self,
        keyword: str,
        offset: int = 0,
        max_results: int = 25,
    ) -> SearchResult:
        """Search transcribed document text."""
        return self._search.search(
            keyword=keyword,
            transcribed_only=True,
            offset=offset,
            max_results=max_results,
        )

    def search_metadata(
        self,
        keyword: str,
        offset: int = 0,
        max_results: int = 25,
    ) -> SearchResult:
        """Search document metadata (titles, names, places)."""
        return self._search.search(
            keyword=keyword,
            transcribed_only=False,
            offset=offset,
            max_results=max_results,
        )

    def browse_document(
        self,
        reference_code: str,
        pages: str = "1-20",
        highlight_term: str | None = None,
        max_pages: int = 20,
    ) -> BrowseResult:
        """Browse specific pages of a document."""
        return self._browse.browse_document(
            reference_code=reference_code,
            pages=pages,
            highlight_term=highlight_term,
            max_pages=max_pages,
        )

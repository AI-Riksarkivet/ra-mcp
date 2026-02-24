"""
Thin facade over SearchOperations and BrowseOperations for TUI use.

All methods are synchronous (called from Textual workers via run_worker(thread=True)).
Uses a dedicated event loop running in a background thread so the httpx.AsyncClient
connection pool stays bound to one loop across all calls.
"""

import asyncio
import threading
from collections.abc import Coroutine

from ra_mcp_browse_lib.browse_operations import BrowseOperations
from ra_mcp_browse_lib.models import BrowseResult
from ra_mcp_common.utils.http_client import HTTPClient
from ra_mcp_search_lib.models import SearchResult
from ra_mcp_search_lib.search_operations import SearchOperations


class ArchiveService:
    """Unified access to search and browse operations.

    Holds a single shared HTTPClient and a persistent event loop
    so the httpx connection pool stays valid across calls.
    """

    def __init__(self) -> None:
        # Dedicated event loop running in a daemon thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        self._http = HTTPClient()
        self._search = SearchOperations(self._http)
        self._browse = BrowseOperations(self._http)

    def _run[T](self, coro: Coroutine[object, object, T]) -> T:
        """Submit a coroutine to the dedicated loop and block until done."""
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def search_transcribed(
        self,
        keyword: str,
        offset: int = 0,
        limit: int = 25,
    ) -> SearchResult:
        """Search transcribed document text."""
        return self._run(
            self._search.search(
                keyword=keyword,
                transcribed_only=True,
                offset=offset,
                limit=limit,
            )
        )

    def search_metadata(
        self,
        keyword: str,
        offset: int = 0,
        limit: int = 25,
    ) -> SearchResult:
        """Search document metadata (titles, names, places)."""
        return self._run(
            self._search.search(
                keyword=keyword,
                transcribed_only=False,
                only_digitised=False,
                offset=offset,
                limit=limit,
            )
        )

    def browse_document(
        self,
        reference_code: str,
        pages: str = "1-20",
        highlight_term: str | None = None,
        max_pages: int = 20,
    ) -> BrowseResult:
        """Browse specific pages of a document."""
        return self._run(
            self._browse.browse_document(
                reference_code=reference_code,
                pages=pages,
                highlight_term=highlight_term,
                max_pages=max_pages,
            )
        )

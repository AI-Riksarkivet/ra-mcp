"""
CLI progress indicators for long-running operations.

Provides Rich progress bar wrappers for search and browse operations.
"""

from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ra_mcp_core.models import SearchResult, BrowseResult
from ..services import SearchOperations, BrowseOperations


def perform_search_with_progress(
    search_operations: SearchOperations,
    keyword: str,
    max_results: int,
    max_hits_per_document: Optional[int],
    console: Console,
) -> SearchResult:
    """Execute search operation with progress indicator.

    Args:
        search_operations: SearchOperations instance
        keyword: Search term
        max_results: Maximum search results to return
        max_hits_per_document: Maximum hits per document
        console: Rich Console instance for output

    Returns:
        SearchResult with hits and metadata
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Search across all volumes
        search_task = progress.add_task(f"Searching for '{keyword}' across all transcribed volumes...", total=None)

        search_result = search_operations.search_transcribed(
            keyword=keyword,
            max_results=max_results,
            max_hits_per_document=max_hits_per_document,
        )

        # Update with detailed results
        hits_count = len(search_result.hits)
        docs_count = search_result.total_hits
        progress.update(
            search_task,
            description=f"✓ Found {hits_count} page hits across {docs_count} volumes",
        )

    return search_result


def load_document_with_progress(
    browse_operations: BrowseOperations,
    reference_code: str,
    pages: str,
    search_term: Optional[str],
    max_display: int,
    console: Console,
) -> BrowseResult:
    """Load document with progress indicator.

    Args:
        browse_operations: BrowseOperations instance
        reference_code: Document reference code
        pages: Page specification (e.g., "1-10" or "5,7,9")
        search_term: Optional term to highlight
        max_display: Maximum pages to display
        console: Rich Console instance for output

    Returns:
        BrowseResult with page contexts and metadata
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        loading_task = progress.add_task("Loading document information...", total=None)

        browse_result = browse_operations.browse_document(
            reference_code=reference_code,
            pages=pages,
            highlight_term=search_term,
            max_pages=max_display,
        )

        progress.update(
            loading_task,
            description=f"✓ Found manifest_id: {browse_result.manifest_id}",
        )

    return browse_result

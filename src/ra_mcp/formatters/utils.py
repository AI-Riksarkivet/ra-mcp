"""
Shared formatting utilities used across different formatters.
"""

from typing import List, Set, Dict
from ..models import SearchHit


def trim_page_number(page_number: str) -> str:
    """
    Remove leading zeros from page number, keeping at least one digit.

    Args:
        page_number: Page number string, possibly with leading zeros

    Returns:
        Page number without leading zeros
    """
    return page_number.lstrip("0") or "0"


def trim_page_numbers(page_numbers: List[str]) -> List[str]:
    """
    Remove leading zeros from multiple page numbers.

    Args:
        page_numbers: List of page number strings

    Returns:
        List of trimmed page numbers
    """
    return [trim_page_number(p) for p in page_numbers]


def get_unique_page_numbers(hits: List[SearchHit]) -> List[str]:
    """
    Get unique page numbers from hits, preserving order and trimming zeros.

    Args:
        hits: List of search hits

    Returns:
        List of unique, trimmed page numbers in order
    """
    seen: Set[str] = set()
    result = []
    for hit in hits:
        if hit.page_number not in seen:
            result.append(trim_page_number(hit.page_number))
            seen.add(hit.page_number)
    return result


def truncate_text(text: str, max_length: int, add_ellipsis: bool = True) -> str:
    """
    Truncate text to maximum length, optionally adding ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length
        add_ellipsis: Whether to add "..." when truncating

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    if add_ellipsis and max_length > 3:
        return text[: max_length - 3] + "..."
    return text[:max_length]


def extract_institution(hit: SearchHit) -> str:
    """
    Extract institution name from a search hit.

    Args:
        hit: Search hit containing metadata

    Returns:
        Institution name or empty string
    """
    if hit.archival_institution:
        return hit.archival_institution[0].get("caption", "")
    elif hit.hierarchy:
        return hit.hierarchy[0].get("caption", "")
    return ""


def format_page_list(page_numbers: List[str], max_pages: int = 5) -> str:
    """
    Format a list of page numbers for display.

    Args:
        page_numbers: List of page numbers
        max_pages: Maximum number of pages to show before truncating

    Returns:
        Formatted string like "1, 2, 3, 4, 5..."
    """
    if len(page_numbers) <= max_pages:
        return ", ".join(page_numbers)

    shown_pages = page_numbers[:max_pages]
    return ", ".join(shown_pages) + "..."


def group_hits_by_reference(hits: List[SearchHit]) -> Dict[str, List[SearchHit]]:
    """
    Group search hits by reference code.

    Args:
        hits: List of search hits

    Returns:
        Dictionary mapping reference codes to lists of hits
    """
    grouped: Dict[str, List[SearchHit]] = {}
    for hit in hits:
        ref_code = hit.reference_code
        if ref_code not in grouped:
            grouped[ref_code] = []
        grouped[ref_code].append(hit)
    return grouped


def sort_hits_by_page(hits: List[SearchHit]) -> List[SearchHit]:
    """
    Sort hits by page number (handling numeric sorting).

    Args:
        hits: List of search hits

    Returns:
        Sorted list of hits
    """
    return sorted(hits, key=lambda h: int(h.page_number) if h.page_number.isdigit() else 0)


def format_example_browse_command(reference_code: str, page_numbers: List[str], search_term: str = "") -> str:
    """
    Format an example browse command for display.

    Args:
        reference_code: Document reference code
        page_numbers: List of page numbers
        search_term: Optional search term to highlight

    Returns:
        Formatted command string
    """
    if len(page_numbers) == 0:
        return ""

    if len(page_numbers) == 1:
        cmd = f'ra browse "{reference_code}" --page {page_numbers[0]}'
    else:
        pages_str = ",".join(page_numbers[:5])  # Show max 5 pages
        cmd = f'ra browse "{reference_code}" --page "{pages_str}"'

    if search_term:
        cmd += f' --search-term "{search_term}"'

    return cmd

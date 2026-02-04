"""
Page range parsing utilities.
"""

from typing import List, Optional


def parse_page_range(page_range: Optional[str], total_pages: int = 1000) -> List[int]:
    """Parse page range string and return list of page numbers.

    Args:
        page_range: Optional string specifying pages to include. Accepts comma-separated
                   values with single pages (e.g., "5") or ranges (e.g., "1-5").
                   If None, defaults to first 20 pages.
        total_pages: Maximum number of pages available (default: 1000).

    Returns:
        Sorted list of unique page numbers within valid range.

    Examples:
        >>> parse_page_range("1-3,5", 10)
        [1, 2, 3, 5]
        >>> parse_page_range(None, 10)
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> parse_page_range("1-100", 10)
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # Capped at total_pages
    """
    if not page_range:
        return list(range(1, min(total_pages + 1, 21)))

    pages = []
    parts = page_range.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = int(start.strip())
            end = int(end.strip())
            pages.extend(range(start, min(end + 1, total_pages + 1)))
        else:
            page_num = int(part.strip())
            if 1 <= page_num <= total_pages:
                pages.append(page_num)

    return sorted(list(set(pages)))

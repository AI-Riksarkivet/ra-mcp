"""
Page range parsing utilities.
"""


def parse_page_range(page_range: str | None, total_pages: int = 1000) -> list[int]:
    """Parse page range string and return list of page numbers.

    Args:
        page_range: Optional string specifying pages to include. Accepts comma-separated
                   values with single pages (e.g., "5") or ranges (e.g., "1-5").
                   If None, defaults to first 20 pages.
        total_pages: Maximum number of pages available (default: 1000).

    Returns:
        Sorted list of unique page numbers within valid range.

    Raises:
        ValueError: If page_range contains no valid page numbers.

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
    invalid_parts = []
    parts = page_range.split(",")

    for part in parts:
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                start_str, end_str = part.split("-", 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                if start < 1 or end < 1:
                    invalid_parts.append(part)
                    continue
                pages.extend(range(start, min(end + 1, total_pages + 1)))
            else:
                page_num = int(part.strip())
                if 1 <= page_num <= total_pages:
                    pages.append(page_num)
                elif page_num < 1:
                    invalid_parts.append(part)
        except ValueError:
            invalid_parts.append(part)

    if not pages and invalid_parts:
        raise ValueError(f"Invalid page specification: {', '.join(invalid_parts)}. Use numbers like '1-5' or '1,3,5'.")

    return sorted(set(pages))

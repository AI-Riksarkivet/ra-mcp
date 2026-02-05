"""
Shared formatting utilities used across different formatters.
"""

from typing import List


def trim_page_number(page_number: str) -> str:
    """
    Remove leading underscores and zeros from page number, keeping at least one digit.

    Args:
        page_number: Page number string, possibly with leading underscores/zeros (e.g., "_00012")

    Returns:
        Page number without leading underscores/zeros (e.g., "12")
    """
    return page_number.lstrip("_0") or "0"


def trim_page_numbers(page_numbers: List[str]) -> List[str]:
    """
    Remove leading zeros from multiple page numbers.

    Args:
        page_numbers: List of page number strings

    Returns:
        List of trimmed page numbers
    """
    return [trim_page_number(p) for p in page_numbers]


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

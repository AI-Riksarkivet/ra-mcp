"""
Page range parsing utilities.
"""

from typing import List, Optional


def parse_page_range(page_range: Optional[str], total_pages: int = 1000) -> List[int]:
    """Parse page range string and return list of page numbers.
    ..Defaults to first 20 pages
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

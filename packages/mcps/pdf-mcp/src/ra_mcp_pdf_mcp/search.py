"""HTML-to-text helpers for block-level PDF text extraction."""

from __future__ import annotations

import re


_STRIP_HTML = re.compile(r"<[^>]+>")


def html_to_text(html: str) -> str:
    """Strip HTML tags, returning plain text."""
    return _STRIP_HTML.sub(" ", html).strip()


def _count_occurrences(text: str, term: str) -> int:
    count = 0
    start = 0
    while True:
        idx = text.find(term, start)
        if idx == -1:
            break
        count += 1
        start = idx + len(term)
    return count

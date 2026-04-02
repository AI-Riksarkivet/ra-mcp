"""Simple module-level state for the current SBL article (single-user)."""

from __future__ import annotations


_current_article: dict | None = None


def set_article(article: dict) -> dict:
    """Store the current article and return it."""
    global _current_article
    _current_article = article
    return article


def get_article() -> dict | None:
    """Return the current article, or None if no article is loaded."""
    return _current_article

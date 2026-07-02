"""Per-view state for SBL article viewer."""

from __future__ import annotations

import uuid


_views: dict[str, dict] = {}
_latest_view_id: str = ""


def create_view(article: dict) -> tuple[str, dict]:
    """Create a new view with a unique ID, store the article, return (view_id, article)."""
    view_id = uuid.uuid4().hex[:12]
    _views[view_id] = article
    global _latest_view_id
    _latest_view_id = view_id
    return view_id, article


def set_article(view_id: str, article: dict) -> dict:
    """Update the article for a specific view."""
    _views[view_id] = article
    return article


def get_article(view_id: str) -> dict | None:
    """Return the article for a specific view."""
    return _views.get(view_id)

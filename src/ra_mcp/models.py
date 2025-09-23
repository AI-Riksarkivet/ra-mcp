"""
Data models for Riksarkivet MCP server.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SearchHit:
    """A search hit with context."""
    pid: str
    title: str
    reference_code: str
    page_number: str
    snippet_text: str
    full_page_text: Optional[str] = None
    alto_url: Optional[str] = None
    image_url: Optional[str] = None
    bildvisning_url: Optional[str] = None
    score: float = 0.0
    hierarchy: Optional[List[Dict[str, str]]] = None
    note: Optional[str] = None
    collection_url: Optional[str] = None
    manifest_url: Optional[str] = None
    archival_institution: Optional[List[Dict[str, str]]] = None
    date: Optional[str] = None


@dataclass
class PageContext:
    """Full page context around a search hit."""
    page_number: int
    page_id: str
    reference_code: str
    full_text: str
    alto_url: str
    image_url: str
    bildvisning_url: str = ""
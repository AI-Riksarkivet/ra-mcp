"""
Data models for Riksarkivet MCP server.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel


class SearchHit(BaseModel):
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


class PageContext(BaseModel):
    page_number: int
    page_id: str
    reference_code: str
    full_text: str
    alto_url: str
    image_url: str
    bildvisning_url: str = ""


class DocumentMetadata(BaseModel):
    """Document metadata containing archival information."""

    title: Optional[str] = None
    hierarchy: Optional[List[Dict[str, str]]] = None
    archival_institution: Optional[List[Dict[str, str]]] = None
    date: Optional[str] = None
    note: Optional[str] = None
    collection_url: Optional[str] = None
    manifest_url: Optional[str] = None


class SearchOperation(BaseModel):
    hits: List[SearchHit]
    total_hits: int
    keyword: str
    offset: int
    enriched: bool = False


class BrowseOperation(BaseModel):
    contexts: List[PageContext]
    reference_code: str
    pages_requested: str
    pid: Optional[str] = None
    manifest_id: Optional[str] = None
    document_metadata: Optional[DocumentMetadata] = None


class SearchSummary(BaseModel):
    """Summary information from a search operation."""

    keyword: str
    total_hits: int
    page_hits_returned: int
    documents_returned: int
    enriched: bool
    offset: int
    grouped_hits: Dict[str, List[SearchHit]]

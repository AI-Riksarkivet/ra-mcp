"""
CLI command for Riksarkivet search.
"""

from .app import search_app
from .search_cmd import search

__all__ = ["search_app", "search"]

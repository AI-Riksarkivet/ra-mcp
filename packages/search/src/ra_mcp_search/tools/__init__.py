"""
MCP tools for Riksarkivet search and browse operations.
"""

from .search_tool import register_search_tool
from .browse_tool import register_browse_tool

__all__ = ["register_search_tool", "register_browse_tool"]

"""
MCP tools for Riksarkivet search.
"""

from .search_tool import register_search_tool
from .tools import search_mcp


__all__ = ["register_search_tool", "search_mcp"]

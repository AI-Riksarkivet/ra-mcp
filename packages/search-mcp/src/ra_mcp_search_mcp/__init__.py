"""
MCP tools for Riksarkivet search and browse.
"""

from .mcp import search_mcp
from .search_tool import register_search_tool
from .browse_tool import register_browse_tool

__all__ = ["search_mcp", "register_search_tool", "register_browse_tool"]

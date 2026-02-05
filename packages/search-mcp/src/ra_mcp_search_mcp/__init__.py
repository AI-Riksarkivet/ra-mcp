"""
MCP tools for Riksarkivet search.
"""

from .mcp import search_mcp
from .search_tool import register_search_tool

__all__ = ["search_mcp", "register_search_tool"]

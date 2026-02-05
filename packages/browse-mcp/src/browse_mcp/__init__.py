"""
MCP tool for browsing Riksarkivet document pages.
"""

from .mcp import browse_mcp
from .browse_tool import register_browse_tool

__all__ = ["browse_mcp", "register_browse_tool"]

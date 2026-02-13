"""
MCP tool for browsing Riksarkivet document pages.
"""

from .browse_tool import register_browse_tool
from .mcp import browse_mcp


__all__ = ["browse_mcp", "register_browse_tool"]

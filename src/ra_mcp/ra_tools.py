"""
MCP tool definitions for RA-MCP server.
Provides search and browse functionality for Riksarkivet documents.

This module now imports the refactored tools that use shared business logic.
"""

# Import the refactored MCP instance and tools
try:
    # Try relative import first (when used as module)
    from .mcp_tools import ra_mcp
except ImportError:
    # Fall back to direct import (when run as script)
    from mcp_tools import ra_mcp

# All tools are now defined in mcp_tools.py using shared business logic
# This eliminates code duplication between CLI and MCP interfaces
"""
RA-MCP Server: Riksarkivet MCP server composition and CLI.

Provides the main MCP server that composes all tool servers
and the CLI entry point.
"""

from importlib.metadata import version


__version__ = version("ra-mcp")

from .server import main, main_server, run_server, setup_server


__all__ = [
    "main",
    "main_server",
    "run_server",
    "setup_server",
]

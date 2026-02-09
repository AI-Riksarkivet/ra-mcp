"""
RA-MCP Server: Riksarkivet MCP server composition and CLI.

Provides the main MCP server that composes all tool servers
and the CLI entry point.
"""

from importlib.metadata import version

__version__ = version("ra-mcp")

from .server import main_server, setup_server, run_server, main

__all__ = [
    "main_server",
    "setup_server",
    "run_server",
    "main",
]

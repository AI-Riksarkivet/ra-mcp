"""
RA-MCP Server: Riksarkivet MCP server composition and CLI.

Provides the main MCP server that composes all tool servers
and the CLI entry point.
"""

__version__ = "0.2.7"

from .server import main_server, setup_server, main

__all__ = [
    "main_server",
    "setup_server",
    "main",
]

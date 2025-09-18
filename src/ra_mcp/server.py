#!/usr/bin/env python3
"""
RA-MCP Server
Main entry point for the Riksarkivet MCP server.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from ra_tools import ra_mcp


def main():
    """Main entry point for the server."""
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        print("Starting RA-MCP HTTP/SSE server on http://localhost:8000")
        print("Connect with: claude mcp add --transport sse ra-mcp http://localhost:8000/sse")
        ra_mcp.run(transport="sse", host="localhost", port=8000)
    else:
        print("Starting RA-MCP stdio server")
        print("This mode is for direct integration with Claude Desktop")
        ra_mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
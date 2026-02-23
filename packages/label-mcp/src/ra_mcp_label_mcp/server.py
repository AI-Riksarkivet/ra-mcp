"""Standalone server for ra-label-mcp.

Run this module directly to start the Label Studio MCP server in isolation,
useful for development and testing without the full composed server.

    python -m ra_mcp_label_mcp.server
    python -m ra_mcp_label_mcp.server --stdio
"""

import argparse
import logging
import os

from .tools import label_mcp


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Riksarkivet Label Studio MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run with stdio transport (default is HTTP)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3003")), help="Port for HTTP server (default: 3003)")
    args = parser.parse_args()

    if args.stdio:
        label_mcp.run(transport="stdio")
    else:
        logger.info("MCP Server listening on http://localhost:%d/mcp", args.port)
        label_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()

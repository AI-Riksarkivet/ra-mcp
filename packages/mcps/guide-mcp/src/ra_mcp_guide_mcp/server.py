"""Standalone server for ra-guide-mcp.

Run this module directly to start the guide MCP server in isolation,
useful for development and testing without the full composed server.

    python -m ra_mcp_guide_mcp.server
    python -m ra_mcp_guide_mcp.server --stdio
"""

import argparse
import logging
import os

from .tools import guide_mcp


logging.basicConfig(level=logging.INFO)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Riksarkivet Guide MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run with stdio transport (default is HTTP)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3001")), help="Port for HTTP server (default: 3001)")
    args = parser.parse_args()

    if args.stdio:
        guide_mcp.run(transport="stdio")
    else:
        logger.info("MCP Server listening on http://localhost:%d/mcp", args.port)
        guide_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()

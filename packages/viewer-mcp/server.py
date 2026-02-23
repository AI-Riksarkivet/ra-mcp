import argparse
import logging
import os

from src import mcp

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Riksarkivet Document Viewer MCP Server")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run with stdio transport (default is HTTP)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "3001")),
        help="Port for HTTP server (default: 3001)",
    )
    args = parser.parse_args()

    if args.stdio:
        mcp.run(transport="stdio")
    else:
        logger.info("MCP Server listening on http://localhost:%d/mcp", args.port)
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=args.port,
            path="/mcp",
        )


if __name__ == "__main__":
    main()

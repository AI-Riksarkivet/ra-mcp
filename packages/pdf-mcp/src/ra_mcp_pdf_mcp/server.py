"""Standalone server for ra-mcp-pdf-mcp.

Run this module directly to start the PDF viewer MCP server in isolation,
useful for development and testing without the full composed server.

    python -m ra_mcp_pdf_mcp.server
    python -m ra_mcp_pdf_mcp.server --stdio
"""

import argparse
import logging
import os

from starlette.responses import Response

from ra_mcp_pdf_mcp import pdf_mcp
from ra_mcp_pdf_mcp.proxy import pdf_proxy_handler


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def _register_proxy_route() -> None:
    """Register the PDF proxy route for speed optimization."""

    @pdf_mcp.custom_route("/pdf-proxy/{view_id}", methods=["GET"])
    async def _pdf_proxy(request) -> Response:  # type: ignore[type-arg]
        return await pdf_proxy_handler(request)


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF Viewer MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run with stdio transport (default is HTTP)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3001")), help="Port for HTTP server (default: 3001)")
    args = parser.parse_args()

    if args.stdio:
        pdf_mcp.run(transport="stdio")
    else:
        _register_proxy_route()
        logger.info("MCP Server listening on http://localhost:%d/mcp", args.port)
        pdf_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()

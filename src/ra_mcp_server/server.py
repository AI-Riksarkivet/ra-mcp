"""
Riksarkivet MCP Server - Main Entry Point

This server uses composition to combine multiple tool servers:
- Search tools for transcribed document search and browsing
- Future tools can be added as separate servers

Environment variables for debugging:
- RA_MCP_LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR) - default: INFO
- RA_MCP_LOG_API: Enable API call logging to file (ra_mcp_api.log)
- RA_MCP_TIMEOUT: Override default timeout in seconds (default: 60)
"""

import asyncio
import logging
import argparse
import os
import sys
from starlette.responses import FileResponse
from fastmcp import FastMCP

from ra_mcp_search_mcp.mcp import search_mcp
from ra_mcp_browse_mcp.mcp import browse_mcp
from ra_mcp_guide.mcp import guide_mcp


def setup_logging():
    """Configure logging for the MCP server with environment variable support."""
    log_level = os.getenv("RA_MCP_LOG_LEVEL", "INFO").upper()
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stderr),  # Always log to stderr for Hugging Face
        ],
    )

    logger = logging.getLogger("ra-mcp")
    logger.info(f"Logging configured at level: {log_level}")
    logger.info(f"Timeout setting: {os.getenv('RA_MCP_TIMEOUT', '60')}s")
    logger.info(f"API logging: {'enabled' if os.getenv('RA_MCP_LOG_API') else 'disabled'}")

    return logger


logger = setup_logging()

main_server = FastMCP(
    name="riksarkivet-mcp",
    instructions="""
    🏛️ Riksarkivet MCP Server

    A MCP server that provides access to the Swedish National Archives (Riksarkivet) data.
    This server combines multiple specialized tool servers to provide a unified interface.

    Available tool categories:
    - Search Tools: Search transcribed historical documents
    - Browse Tools: Browse and view document pages with full text
    - Guide Resources: Historical documentation and guides about Swedish archives
    """,
)


@main_server.custom_route("/", methods=["GET"])
async def root(_):
    return FileResponse("assets/index.html")


async def setup_server():
    """Setup server composition by importing all tool servers."""
    logger.info("Setting up server composition...")

    # Import search tools without prefix (they already have descriptive names)
    await main_server.import_server(search_mcp)
    logger.info("Imported search tools")

    # Import browse tools without prefix (they already have descriptive names)
    await main_server.import_server(browse_mcp)
    logger.info("Imported browse tools")

    # Import guide resources
    await main_server.import_server(guide_mcp)
    logger.info("Imported guide resources")

    # Future tool servers can be imported here with appropriate prefixes
    # Example:
    # await main_server.import_server(ocr_server, prefix="ocr")
    # logger.info("Imported OCR tools with prefix 'ocr'")
    # await main_server.import_server(iiif_server, prefix="iiif")
    # logger.info("Imported IIIF tools with prefix 'iiif'")


def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="Riksarkivet MCP Server")
    parser.add_argument("--http", action="store_true", help="Use HTTP/SSE transport instead of stdio")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport (default: 8000)")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP transport (default: 0.0.0.0)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("Initializing Riksarkivet MCP Server...")
    asyncio.run(setup_server())

    if args.http:
        logger.info(f"Starting Riksarkivet MCP HTTP/SSE server on http://{args.host}:{args.port}")
        main_server.run(transport="streamable-http", host=args.host, port=args.port, path="/mcp")
    else:
        logger.info("Starting Riksarkivet MCP stdio server")
        logger.info("Mode: Direct integration with Claude Desktop")
        main_server.run(transport="stdio")


if __name__ == "__main__":
    main()

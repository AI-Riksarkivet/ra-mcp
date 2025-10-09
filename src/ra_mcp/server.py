"""
Riksarkivet MCP Server - Main Entry Point

This server uses composition to combine multiple tool servers:
- Search tools for transcribed document search and browsing
- Future tools can be added as separate servers
"""

import asyncio
import logging
import argparse
from starlette.responses import FileResponse
from fastmcp import FastMCP

from ra_mcp.search_tools import search_mcp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ra-mcp")

main_server = FastMCP(
    name="riksarkivet-mcp",
    instructions="""
    🏛️ Riksarkivet MCP Server

    A comprehensive MCP server providing access to the Swedish National Archives (Riksarkivet) data.
    This server combines multiple specialized tool servers to provide a unified interface.

    Available tool categories:
    - Search Tools: Search and browse transcribed historical documents
    - (More tool categories can be added here)
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

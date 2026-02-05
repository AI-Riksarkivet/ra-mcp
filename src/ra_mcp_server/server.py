"""
Riksarkivet MCP Server - Composable Main Entry Point

This server uses composition to combine multiple tool servers.
Modules can be enabled/disabled via command-line flags for flexible deployment.

Default modules:
- search: Search tools for transcribed document search
- browse: Browse tools for viewing document pages
- guide: Historical documentation and archival guides

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
from typing import List, Dict, Any
from starlette.responses import FileResponse
from fastmcp import FastMCP

# Import available modules (lazy imports handled in setup)
from ra_mcp_search_mcp.mcp import search_mcp
from ra_mcp_browse_mcp.mcp import browse_mcp
from ra_mcp_guide_mcp.mcp import guide_mcp


# Registry of available modules
AVAILABLE_MODULES = {
    "search": {
        "server": search_mcp,
        "description": "Search transcribed historical documents with advanced query syntax",
        "default": True,
    },
    "browse": {
        "server": browse_mcp,
        "description": "View full page transcriptions by reference code",
        "default": True,
    },
    "guide": {
        "server": guide_mcp,
        "description": "Access historical documentation and archival guides",
        "default": True,
    },
    # Future modules can be added here:
    # "metadata": {
    #     "server": metadata_mcp,
    #     "description": "Advanced metadata search and filtering",
    #     "default": False,
    # },
}


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


def build_instructions(enabled_modules: List[str]) -> str:
    """Build dynamic instructions based on enabled modules.

    Args:
        enabled_modules: List of module names that are enabled.

    Returns:
        Comprehensive instruction string describing available capabilities.
    """
    module_descriptions = []
    for module_name in enabled_modules:
        if module_name in AVAILABLE_MODULES:
            module = AVAILABLE_MODULES[module_name]
            module_descriptions.append(f"    - {module_name}: {module['description']}")

    modules_section = "\n".join(module_descriptions) if module_descriptions else "    (No modules enabled)"

    return f"""
    🏛️ Riksarkivet MCP Server

    A Model Context Protocol server providing access to the Swedish National Archives (Riksarkivet).
    This server combines multiple specialized tool servers into a unified interface for historical research.

    📋 ENABLED MODULES:

{modules_section}

    Each tool and resource includes detailed documentation. Use MCP's tool/list and resource/list
    to discover available capabilities, or consult individual tool descriptions for usage guidance.

    """


def create_server(enabled_modules: List[str]) -> FastMCP:
    """Create a FastMCP server with dynamic instructions.

    Args:
        enabled_modules: List of module names to enable.

    Returns:
        Configured FastMCP server instance.
    """
    return FastMCP(
        name="riksarkivet-mcp",
        instructions=build_instructions(enabled_modules),
    )


# Global server instance (configured in main)
main_server = None


async def setup_server(server: FastMCP, enabled_modules: List[str]):
    """Setup server composition by importing selected tool servers.

    Args:
        server: The FastMCP server instance to configure.
        enabled_modules: List of module names to import.
    """
    logger.info("Setting up server composition...")
    logger.info(f"Enabled modules: {', '.join(enabled_modules)}")

    imported_count = 0
    for module_name in enabled_modules:
        if module_name not in AVAILABLE_MODULES:
            logger.warning(f"⚠ Unknown module '{module_name}' - skipping")
            continue

        module = AVAILABLE_MODULES[module_name]
        try:
            await server.import_server(module["server"])
            logger.info(f"✓ Imported {module['server'].name}")
            imported_count += 1
        except Exception as e:
            logger.error(f"✗ Failed to import {module_name}: {e}")

    if imported_count == 0:
        logger.warning("⚠ No modules were successfully imported!")
    else:
        logger.info(f"Server composition complete. {imported_count} module(s) imported.")


def setup_custom_routes(server: FastMCP):
    """Setup custom HTTP routes for the server.

    Args:
        server: The FastMCP server instance to add routes to.
    """
    @server.custom_route("/", methods=["GET"])
    async def root(_):
        return FileResponse("assets/index.html")


def main():
    """Main entry point for the server."""
    global main_server

    # Get default modules
    default_modules = [name for name, info in AVAILABLE_MODULES.items() if info["default"]]

    parser = argparse.ArgumentParser(
        description="Riksarkivet MCP Server - Composable access to Swedish National Archives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available modules:
{chr(10).join(f"  {name:12} - {info['description']}" for name, info in AVAILABLE_MODULES.items())}

Examples:
  ra serve                              # Start with all default modules
  ra serve --modules search,browse      # Start with only search and browse
  ra serve --port 8000                  # Start HTTP server on port 8000
  ra serve --modules search --port 8000 # Custom modules with HTTP transport
        """,
    )
    parser.add_argument("--http", action="store_true", help="Use HTTP/SSE transport instead of stdio")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transport (default: 8000)")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP transport (default: 0.0.0.0)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--modules",
        type=str,
        default=",".join(default_modules),
        help=f"Comma-separated list of modules to enable (default: {','.join(default_modules)})",
    )
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="List available modules and exit",
    )

    args = parser.parse_args()

    # Handle --list-modules
    if args.list_modules:
        print("Available modules:")
        for name, info in AVAILABLE_MODULES.items():
            default_marker = " (default)" if info["default"] else ""
            print(f"  {name:12} - {info['description']}{default_marker}")
        return

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Parse enabled modules
    enabled_modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    logger.info("Initializing Riksarkivet MCP Server...")

    # Create server with dynamic instructions
    main_server = create_server(enabled_modules)

    # Setup custom routes
    setup_custom_routes(main_server)

    # Import selected modules
    asyncio.run(setup_server(main_server, enabled_modules))

    if args.http:
        logger.info(f"Starting Riksarkivet MCP HTTP/SSE server on http://{args.host}:{args.port}")
        main_server.run(transport="streamable-http", host=args.host, port=args.port, path="/mcp")
    else:
        logger.info("Starting Riksarkivet MCP stdio server")
        logger.info("Mode: Direct integration with Claude Desktop")
        main_server.run(transport="stdio")


if __name__ == "__main__":
    main()

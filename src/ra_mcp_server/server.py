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

import atexit
import logging
import argparse
import os
import sys
from typing import List
from starlette.responses import FileResponse, JSONResponse
from fastmcp import FastMCP

from ra_mcp_server.telemetry import init_telemetry, shutdown_telemetry

# Import available modules (lazy imports handled in setup)
from search_mcp.mcp import search_mcp
from browse_mcp.mcp import browse_mcp
from guide_mcp.mcp import guide_mcp


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
_mounted_modules: List[str] = []


def setup_server(server: FastMCP, enabled_modules: List[str]):
    """Setup server composition by mounting selected tool servers.

    Args:
        server: The FastMCP server instance to configure.
        enabled_modules: List of module names to mount.
    """
    logger.info("Setting up server composition...")
    logger.info(f"Enabled modules: {', '.join(enabled_modules)}")

    _mounted_modules.clear()
    for module_name in enabled_modules:
        if module_name not in AVAILABLE_MODULES:
            logger.warning(f"⚠ Unknown module '{module_name}' - skipping")
            continue

        module_config = AVAILABLE_MODULES[module_name]
        module_server: FastMCP = module_config["server"]  # type: ignore[assignment]
        try:
            server.mount(module_server, namespace=module_name)
            logger.info(f"✓ Mounted {module_server.name} (namespace={module_name})")
            _mounted_modules.append(module_name)
        except Exception as e:
            logger.error(f"✗ Failed to mount {module_name}: {e}")

    if not _mounted_modules:
        logger.warning("⚠ No modules were successfully mounted!")
    else:
        logger.info(f"Server composition complete. {len(_mounted_modules)} module(s) mounted.")


def setup_custom_routes(server: FastMCP):
    """Setup custom HTTP routes for the server.

    Args:
        server: The FastMCP server instance to add routes to.
    """

    @server.custom_route("/", methods=["GET"])
    async def root(_):
        return FileResponse("assets/index.html")

    @server.custom_route("/health", methods=["GET"])
    async def health(_):
        return JSONResponse({"status": "ok"})

    @server.custom_route("/ready", methods=["GET"])
    async def ready(_):
        if _mounted_modules:
            return JSONResponse({"status": "ready", "modules": _mounted_modules})
        return JSONResponse({"status": "not ready", "modules": []}, status_code=503)


def run_server(
    *,
    http: bool = False,
    port: int = 8000,
    host: str = "0.0.0.0",
    verbose: bool = False,
    modules: str | None = None,
):
    """Run the MCP server with the given configuration.

    Args:
        http: Use HTTP/SSE transport instead of stdio.
        port: Port for HTTP transport.
        host: Host for HTTP transport.
        verbose: Enable verbose logging.
        modules: Comma-separated list of modules to enable.
    """
    init_telemetry()
    atexit.register(shutdown_telemetry)

    global main_server

    if verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    default_modules = [name for name, info in AVAILABLE_MODULES.items() if info["default"]]
    enabled_modules = [m.strip() for m in modules.split(",") if m.strip()] if modules else default_modules

    logger.info("Initializing Riksarkivet MCP Server...")

    main_server = create_server(enabled_modules)
    setup_custom_routes(main_server)
    setup_server(main_server, enabled_modules)

    if http:
        logger.info(f"Starting Riksarkivet MCP HTTP/SSE server on http://{host}:{port}")
        main_server.run(transport="streamable-http", host=host, port=port, path="/mcp")
    else:
        logger.info("Starting Riksarkivet MCP stdio server")
        logger.info("Mode: Direct integration with Claude Desktop")
        main_server.run(transport="stdio")


def main():
    """CLI entry point for direct invocation (e.g., python -m ra_mcp_server.server)."""
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
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP transport (default: 0.0.0.0)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--modules",
        type=str,
        default=",".join(default_modules),
        help=f"Comma-separated list of modules to enable (default: {','.join(default_modules)})",
    )
    parser.add_argument("--list-modules", action="store_true", help="List available modules and exit")

    args = parser.parse_args()

    if args.list_modules:
        print("Available modules:")
        for name, info in AVAILABLE_MODULES.items():
            default_marker = " (default)" if info["default"] else ""
            print(f"  {name:12} - {info['description']}{default_marker}")
        return

    run_server(http=args.http, port=args.port, host=args.host, verbose=args.verbose, modules=args.modules)


if __name__ == "__main__":
    main()

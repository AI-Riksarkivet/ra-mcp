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

import argparse
import atexit
import logging
import os
import sys
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.providers import FastMCPProvider
from fastmcp.server.providers.skills import SkillsDirectoryProvider
from starlette.responses import FileResponse, JSONResponse

from ra_mcp_browse_mcp.mcp import browse_mcp
from ra_mcp_guide_mcp.mcp import guide_mcp

# Import available modules (lazy imports handled in setup)
from ra_mcp_search_mcp.mcp import search_mcp
from ra_mcp_server.telemetry import init_telemetry, shutdown_telemetry


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
}


def setup_logging() -> logging.Logger:
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
    logger.info("Logging configured at level: %s", log_level)
    logger.info("Timeout setting: %ss", os.getenv("RA_MCP_TIMEOUT", "60"))
    logger.info("API logging: %s", "enabled" if os.getenv("RA_MCP_LOG_API") else "disabled")

    return logger


logger = setup_logging()


def build_instructions(enabled_modules: list[str]) -> str:
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

    ⚠️ RESEARCH INTEGRITY — MANDATORY RULES:

    This is an academic research tool. Accuracy and proper sourcing are paramount.

    1. NEVER fabricate, guess, or hallucinate reference codes, page numbers, dates, names,
       or any archival data. Every claim must come directly from tool results.
    2. ALWAYS cite the exact reference code and page number when presenting information
       from a document (e.g. "SE/RA/420422/01/A I a 1/288, page 66").
    3. ONLY use links that are explicitly returned by the tools (bildvisaren, ALTO XML,
       NAD links, IIIF URLs). NEVER construct or guess URLs — not even by combining
       a base URL with a reference code. If a tool result does not include a link,
       do not invent one.
    4. DISTINGUISH clearly between what the document says (quote or close paraphrase)
       and your own interpretation or translation. Use quotation marks for original text.
    5. If a transcription is unclear, incomplete, or ambiguous, say so explicitly.
       Do not silently fill in gaps with plausible-sounding text.
    6. When translating old Swedish, mark it as a translation and note when
       the meaning is uncertain.
    7. If you cannot find information the user is looking for, say so. Do not
       construct an answer from partial or unrelated results.

    🔍 UNDERSTAND THE RESEARCH GOAL BEFORE SEARCHING:

    Before making your first search, ensure you understand what the user is researching.
    If their intent is vague or unclear, ASK clarifying questions first:
    - What time period are they interested in?
    - What type of documents are they looking for (court records, church records, military, estates)?
    - Are they researching a specific person, family, place, or event?
    - What do they already know that could help narrow the search?

    Every tool call includes a research_context parameter — always fill it in with your
    best understanding of the user's research goal based on the conversation so far.

    """


def create_server(enabled_modules: list[str]) -> FastMCP:
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
_mounted_modules: list[str] = []


def _discover_plugin_skills() -> list[Path]:
    """Discover skill directories from plugins.

    Scans the plugins directory for subdirectories containing skills.
    The plugins directory is resolved from the ``RA_MCP_PLUGINS_DIR``
    environment variable, falling back to ``plugins/`` relative to the
    current working directory.
    """
    plugins_dir = Path(os.getenv("RA_MCP_PLUGINS_DIR", "plugins"))
    if not plugins_dir.is_dir():
        return []
    return sorted(p for p in plugins_dir.glob("*/skills") if p.is_dir())


def setup_server(server: FastMCP, enabled_modules: list[str]) -> None:
    """Setup server composition using explicit providers.

    Each module's FastMCP sub-server is wrapped in a FastMCPProvider and
    registered with a namespace. This gives the same behaviour as mount()
    while exposing the provider layer for future transforms and visibility
    control.

    Args:
        server: The FastMCP server instance to configure.
        enabled_modules: List of module names to register as providers.
    """
    logger.info("Setting up server composition...")
    logger.info("Enabled modules: %s", ", ".join(enabled_modules))

    _mounted_modules.clear()
    for module_name in enabled_modules:
        if module_name not in AVAILABLE_MODULES:
            logger.warning("⚠ Unknown module '%s' - skipping", module_name)
            continue

        module_config = AVAILABLE_MODULES[module_name]
        module_server: FastMCP = module_config["server"]  # type: ignore[assignment]
        try:
            server.add_provider(FastMCPProvider(module_server), namespace=module_name)
            logger.info("✓ Registered %s (namespace=%s)", module_server.name, module_name)
            _mounted_modules.append(module_name)
        except Exception as e:
            logger.error("✗ Failed to register %s: %s", module_name, e)

    # Expose plugin skills as MCP resources
    skill_roots = _discover_plugin_skills()
    if skill_roots:
        server.add_provider(SkillsDirectoryProvider(roots=skill_roots))
        logger.info("✓ Loaded skills from: %s", ", ".join(str(r) for r in skill_roots))

    if not _mounted_modules:
        logger.warning("⚠ No modules were successfully registered!")
    else:
        logger.info("Server composition complete. %d module(s) registered.", len(_mounted_modules))


def setup_custom_routes(server: FastMCP) -> None:
    """Setup custom HTTP routes for the server.

    Args:
        server: The FastMCP server instance to add routes to.
    """

    @server.custom_route("/", methods=["GET"])
    async def root(_) -> FileResponse:
        return FileResponse("assets/index.html")

    @server.custom_route("/health", methods=["GET"])
    async def health(_) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @server.custom_route("/ready", methods=["GET"])
    async def ready(_) -> JSONResponse:
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
) -> None:
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
        logger.info("Starting Riksarkivet MCP HTTP/SSE server on http://%s:%d", host, port)
        main_server.run(transport="streamable-http", host=host, port=port, path="/mcp")
    else:
        logger.info("Starting Riksarkivet MCP stdio server")
        logger.info("Mode: Direct integration with Claude Desktop")
        main_server.run(transport="stdio")


def main() -> None:
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

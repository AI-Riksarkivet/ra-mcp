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

from ra_mcp_browse_mcp.tools import browse_mcp
from ra_mcp_guide_mcp.tools import guide_mcp
from ra_mcp_htr_mcp.tools import htr_mcp
from ra_mcp_pdf_mcp import pdf_mcp

# Import available modules (lazy imports handled in setup)
from ra_mcp_search_mcp.tools import search_mcp
from ra_mcp_server.telemetry import init_telemetry, shutdown_telemetry
from ra_mcp_viewer_mcp import viewer_mcp


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
    "htr": {
        "server": htr_mcp,
        "description": "Transcribe handwritten documents using HTRflow",
        "default": True,
    },
    "viewer": {
        "server": viewer_mcp,
        "description": "Interactive document viewer with zoomable images and text layer overlays",
        "default": True,
        "no_namespace": True,
    },
    "pdf": {
        "server": pdf_mcp,
        "description": "Interactive PDF viewer with search, annotations, and PDF.js rendering",
        "default": True,
        "no_namespace": True,
    },
}

# label-mcp is optional (requires glibc for opencv-python-headless via label-studio-sdk)
try:
    from ra_mcp_label_mcp.tools import label_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["label"] = {
        "server": label_mcp,
        "description": "Import pages to Label Studio for human annotation and feedback",
        "default": True,
    }
except ImportError:
    pass

# diplomatics-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_diplomatics_mcp import diplomatics_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["diplomatics"] = {
        "server": diplomatics_mcp,
        "description": "Search SDHK medieval charters and MPO parchment fragments",
        "default": True,
    }
except ImportError:
    pass

# sbl-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_sbl_mcp import sbl_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["sbl"] = {
        "server": sbl_mcp,
        "description": "Search Svenskt biografiskt lexikon (Swedish Biographical Lexicon)",
        "default": True,
    }
except ImportError:
    pass

# sjomanshus-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_sjomanshus_mcp import sjomanshus_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["sjomanshus"] = {
        "server": sjomanshus_mcp,
        "description": "Search Swedish seamen's house records (voyages and registrations)",
        "default": True,
    }
except ImportError:
    pass

# filmcensur-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_filmcensur_mcp import filmcensur_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["filmcensur"] = {
        "server": filmcensur_mcp,
        "description": "Search Swedish film censorship records 1911-2011 (60K films)",
        "default": True,
    }
except ImportError:
    pass

# rosenberg-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_rosenberg_mcp import rosenberg_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["rosenberg"] = {
        "server": rosenberg_mcp,
        "description": "Search Rosenberg's geographical lexicon of Sweden (66K historical places)",
        "default": True,
    }
except ImportError:
    pass

# court-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_court_mcp import court_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["court"] = {
        "server": court_mcp,
        "description": "Search Swedish court records (Domboksregister 1611-1730, Medelstad 1668-1750)",
        "default": True,
    }
except ImportError:
    pass

# aktiebolag-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_aktiebolag_mcp import aktiebolag_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["aktiebolag"] = {
        "server": aktiebolag_mcp,
        "description": "Search Swedish joint-stock companies 1901-1935 (12.5K companies, 49K board members)",
        "default": True,
    }
except ImportError:
    pass

# faltjagare-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_faltjagare_mcp import faltjagare_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["faltjagare"] = {
        "server": faltjagare_mcp,
        "description": "Search Jämtland field regiment soldier records 1645-1901 (43K soldiers)",
        "default": True,
    }
except ImportError:
    pass

# suffrage-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_suffrage_mcp import suffrage_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["suffrage"] = {
        "server": suffrage_mcp,
        "description": "Search women's suffrage records (Rösträtt petition 1913-1914, FKPR association 1911-1920)",
        "default": True,
    }
except ImportError:
    pass


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

    # Quiet noisy third-party loggers
    for name in ("httpx", "httpcore", "mcp", "gradio_client"):
        logging.getLogger(name).setLevel(logging.WARNING)

    # Optional file handler for API call logging
    if os.getenv("RA_MCP_LOG_API"):
        file_handler = logging.FileHandler("ra_mcp_api.log")
        file_handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
        logging.getLogger().addHandler(file_handler)

    logger = logging.getLogger("ra_mcp.server")
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

    return f"""Riksarkivet MCP Server — access to the Swedish National Archives (Riksarkivet).

ENABLED MODULES:
{modules_section}

WORKFLOW: Start with search_transcribed or search_metadata to find documents.
Use browse_document to read full page transcriptions of interesting results.
Paginate searches (offset 0, 50, 100...) for comprehensive discovery.

TOOL SELECTION:
- Person/family lookup → search_metadata with name="..."
- Place-based search → search_metadata with place="..."
- Full-text in court records → search_transcribed with Solr syntax
- Church records, estate inventories, military → search_metadata (these are cataloged but mostly not AI-transcribed)
- Read document pages → browse_document with reference code from search results
- Medieval charters (before 1540) → diplomatics:search_sdhk with keyword
- Medieval parchment fragments → diplomatics:search_mpo with keyword (German terms)
- View SDHK/MPO documents → view_manifest with IIIF manifest URL from search results
- Biographical lookup (notable Swedes) → sbl:search_sbl with name or keyword
- View SBL article → sbl:view_sbl_article with article_id from search results
- Seamen's voyages (1700s-1900s) → sjomanshus:search_liggare with keyword, filter by ship/rank/port
- Seamen's registrations → sjomanshus:search_matrikel with keyword
- Film censorship records (1911-2011) → filmcensur:search_filmreg with keyword, filter by category/country/age rating
- Historical Swedish places/geography → rosenberg:search_rosenberg with keyword, filter by county/parish
- Västra härad court cases (1611-1730) → court:search_domboksregister with keyword, filter by role/parish
- Medelstad härad court cases (1668-1750) → court:search_medelstad with keyword, filter by case type/parish

COVERAGE: The archive has three access tiers:
- Metadata catalog: 2M+ records (search_metadata) — titles, names, places, dates
- Digitised images: ~73M pages viewable via bildvisaren links
- AI-transcribed text: ~1.6M pages searchable via search_transcribed — currently court records (hovrätt, trolldomskommissionen, poliskammare, magistrat) from 17th-18th centuries
- SDHK catalog: 44,000+ medieval charters (diplomatics:search_sdhk) — summaries, Latin texts, seal descriptions
- MPO catalog: 23,000+ parchment fragments (diplomatics:search_mpo) — codicological descriptions in German
- SBL: 9,400+ biographical articles (sbl:search_sbl) — notable Swedish individuals and families, medieval to 20th century
- Sjömanshus: 688,000+ seamen's records (sjomanshus:search_liggare, sjomanshus:search_matrikel) — voyages, registrations, 1700s-1900s
- Filmcensur: 60,000 film censorship records (filmcensur:search_filmreg) — titles, age ratings, cuts, producers, 1911-2011
- Rosenberg: 66,000 historical places (rosenberg:search_rosenberg) — place names, parishes, hundreds, counties, descriptions, industry flags
- Domboksregister: 88,000 persons in Västra härad court cases 1611-1730 (court:search_domboksregister) — names, roles, parishes, case types, dates
- Medelstad: 91,000 persons in Medelstad härad court cases 1668-1750 (court:search_medelstad) — names, titles, parishes, case summaries

COMPANION SKILLS (invoke /archive-search or /archive-research for detailed guidance):
- archive-search: Solr query syntax, fuzzy matching, old Swedish spelling variants
- archive-research: Research integrity, citing sources, presenting findings

RESEARCH INTEGRITY: Never fabricate reference codes, page numbers, dates, or names.
Cite exact reference codes and page numbers. Only use links returned by tools.
Distinguish document quotes from interpretation. Flag uncertain transcriptions.

Always fill in the research_context parameter on every tool call.
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
            namespace = "" if module_config.get("no_namespace") else module_name
            server.add_provider(FastMCPProvider(module_server), namespace=namespace)
            logger.info("✓ Registered %s (namespace=%s)", module_server.name, namespace or "(none)")
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
        return FileResponse("docs/assets/index.html")

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
    port: int = 7860,
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
    """Thin entry point for ``ra-serve`` (used by Docker and Dagger).

    For interactive use prefer the Typer CLI: ``ra serve --help``.
    """
    parser = argparse.ArgumentParser(description="Riksarkivet MCP Server")
    parser.add_argument("--http", action="store_true", help="Use HTTP transport instead of stdio")
    parser.add_argument("--port", type=int, default=7860, help="Port for HTTP transport (default: 7860)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP transport (default: 0.0.0.0)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--modules", type=str, default=None, help="Comma-separated list of modules to enable")
    args = parser.parse_args()

    run_server(http=args.http, port=args.port, host=args.host, verbose=args.verbose, modules=args.modules)


if __name__ == "__main__":
    main()

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ra-mcp** (Riksarkivet Model Context Protocol) is an MCP server that provides access to transcribed historical documents from the Swedish National Archives (Riksarkivet).

### Architecture

The project is organized as a **uv workspace** with eight modular packages plus a root server:

```
ra-mcp/
├── src/ra_mcp_server/          # Root: Server composition and main CLI
│   ├── server.py               # FastMCP composition entry point
│   └── cli/app.py              # Typer CLI root (ra command)
├── packages/
│   ├── common/                 # ra-mcp-common: Shared HTTP client and utilities
│   ├── search/                 # ra-mcp-search: Search domain (models, clients, operations)
│   ├── browse/                 # ra-mcp-browse: Browse domain (models, clients, operations)
│   ├── search-mcp/             # ra-mcp-search-mcp: MCP tools for search
│   ├── browse-mcp/             # ra-mcp-browse-mcp: MCP tool for browse
│   ├── search-cli/             # ra-mcp-search-cli: CLI command for search
│   ├── browse-cli/             # ra-mcp-browse-cli: CLI command for browse
│   └── guide-mcp/              # ra-mcp-guide-mcp: MCP resources for historical guides
├── resources/                  # Historical guide markdown files
├── pyproject.toml              # Workspace configuration
└── uv.lock                     # Shared lockfile
```

### Package Structure

**ra-mcp-common** (no internal dependencies):
- [http_client.py](packages/common/src/ra_mcp_common/utils/http_client.py): Centralized urllib-based HTTP client with logging

**ra-mcp-search** (depends on common):
- [config.py](packages/search/src/ra_mcp_search/config.py): Search API URL and constants
- [models.py](packages/search/src/ra_mcp_search/models.py): Pydantic models (SearchRecord, RecordsResponse, SearchResult)
- [clients/search_client.py](packages/search/src/ra_mcp_search/clients/search_client.py): SearchAPI client
- [operations/search_operations.py](packages/search/src/ra_mcp_search/operations/search_operations.py): Search business logic

**ra-mcp-browse** (depends on common):
- [config.py](packages/browse/src/ra_mcp_browse/config.py): Browse API URLs and constants
- [models.py](packages/browse/src/ra_mcp_browse/models.py): Pydantic models (BrowseResult, PageContext)
- [clients/](packages/browse/src/ra_mcp_browse/clients/): API clients (ALTOClient, IIIFClient, OAIPMHClient)
- [operations/browse_operations.py](packages/browse/src/ra_mcp_browse/operations/browse_operations.py): Browse business logic
- [url_generator.py](packages/browse/src/ra_mcp_browse/url_generator.py): URL construction helpers

**ra-mcp-search-mcp** (depends on search + fastmcp):
- [mcp.py](packages/search-mcp/src/search_mcp/mcp.py): FastMCP server setup and instructions
- [search_tool.py](packages/search-mcp/src/search_mcp/search_tool.py): `search_transcribed` and `search_metadata` MCP tools
- [formatter.py](packages/search-mcp/src/search_mcp/formatter.py): Search result formatting for LLM output

**ra-mcp-browse-mcp** (depends on browse + fastmcp):
- [mcp.py](packages/browse-mcp/src/browse_mcp/mcp.py): FastMCP server setup and instructions
- [browse_tool.py](packages/browse-mcp/src/browse_mcp/browse_tool.py): `browse_document` MCP tool
- [formatter.py](packages/browse-mcp/src/browse_mcp/formatter.py): Browse result formatting for LLM output

**ra-mcp-search-cli** (depends on search + typer + rich):
- [app.py](packages/search-cli/src/search_cli/app.py): Typer sub-app
- [search_cmd.py](packages/search-cli/src/search_cli/search_cmd.py): `ra search` CLI command
- [formatting/](packages/search-cli/src/search_cli/formatting/): CLI output formatting

**ra-mcp-browse-cli** (depends on browse + typer + rich):
- [app.py](packages/browse-cli/src/browse_cli/app.py): Typer sub-app
- [browse_cmd.py](packages/browse-cli/src/browse_cli/browse_cmd.py): `ra browse` CLI command
- [formatting/](packages/browse-cli/src/browse_cli/formatting/): CLI output formatting

**ra-mcp-guide-mcp** (depends on common + fastmcp):
- [mcp.py](packages/guide-mcp/src/guide_mcp/mcp.py): MCP resources for historical guides from `resources/`

**Root package — ra-mcp** (depends on all MCP and CLI packages):
- [server.py](src/ra_mcp_server/server.py): FastMCP composition server (imports search, browse, guide modules)
- [cli/app.py](src/ra_mcp_server/cli/app.py): Main Typer CLI entry point (`ra` command)

### Package Dependencies

```
ra-mcp-common              (no internal deps)
       ↑
ra-mcp-search              (depends on common)
ra-mcp-browse              (depends on common)
       ↑
ra-mcp-search-mcp          (depends on search + fastmcp)
ra-mcp-browse-mcp          (depends on browse + fastmcp)
ra-mcp-guide-mcp           (depends on common + fastmcp)
ra-mcp-search-cli          (depends on search + typer + rich)
ra-mcp-browse-cli          (depends on browse + typer + rich)
       ↑
ra-mcp (root)              (composes all MCP and CLI packages)
```

## Development Workflow

### Setup

```bash
# Clone repository
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp

# Install dependencies (syncs workspace packages)
uv sync
```

### Running the Server

```bash
# MCP server (stdio) - for Claude Desktop integration
uv run ra serve

# MCP server (HTTP/SSE) - for web clients, testing, and development
uv run ra serve --port 8000

# With verbose logging
uv run ra serve --port 8000 --log
```

### Using the CLI

The project includes a full-featured CLI for searching and browsing documents:

```bash
# Search for documents
uv run ra search "trolldom"
uv run ra search "Stockholm" --max 50

# Browse specific documents
uv run ra browse "SE/RA/310187/1" --page "7,8,52"
uv run ra browse "SE/RA/420422/01" --pages "1-10" --search-term "Stockholm"

# Get help
uv run ra --help
uv run ra search --help
uv run ra browse --help
```

### Testing

**IMPORTANT**: The test infrastructure is currently being set up. Tests will be added in the `packages/*/tests/` directories.

```bash
# Run all tests (when tests exist)
uv run pytest

# Run with coverage (requires pytest-cov)
uv run pytest --cov=ra_mcp_common --cov=ra_mcp_search --cov=ra_mcp_browse --cov-report=html

# Run specific package tests
uv run pytest packages/common/tests/ -v
uv run pytest packages/search/tests/ -v
uv run pytest packages/browse/tests/ -v
```

**Note**: The Dagger pipeline currently accepts zero tests as success until the test suite is implemented.

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint and auto-fix issues
uv run ruff check --fix .

# Type check (ty is configured in pyproject.toml)
uv run ty check
```

### Running CI Checks Locally

**IMPORTANT**: Before committing code, always run CI checks locally to catch issues early.

```bash
# Run full CI pipeline (same as GitHub Actions)
dagger call checks && dagger call test

# Quick check: Run code quality checks only
dagger call checks

# Quick check: Run tests only
dagger call test
```

**Best Practice**: Run `dagger call checks` before every commit to ensure:
- Code is properly formatted
- No linting errors
- Type checking passes
- Tests pass (when implemented)

This matches exactly what runs in GitHub Actions CI, preventing failed builds.

### Debugging

```bash
# Test MCP server with MCP Inspector
npx @modelcontextprotocol/inspector uv run ra serve

# Test HTTP/SSE server with curl
uv run ra serve --port 8000
curl http://localhost:8000/mcp
```

### Testing with Dagger

You can build and test the containerized server using Dagger:

```bash
# Build and test server with automatic health check
dagger call test-server --source=.

# Just build the container
dagger call build --source=.

# Start server as a Dagger service (for testing with other containers)
dagger call serve --source=. --port=7860

# Expose server on host for manual testing
dagger call serve-up --source=. --port=7860 up
```

**Interactive testing with Dagger shell:**
```bash
# Build and get a shell in the container
dagger call build --source=. terminal

# Inside the container, you can:
# - Test the server: ra serve --host 0.0.0.0 --port 7860
# - Run CLI commands: ra search "trolldom"
# - Check environment: python --version
# - Debug issues: ls -la /app
```

## Building and Publishing

### Prerequisites

The project uses [Dagger](https://docs.dagger.io/install) for containerized builds and publishing.

**For Docker publishing:**
```bash
export DOCKER_USERNAME="your-dockerhub-username"
export DOCKER_PASSWORD="your-dockerhub-token-or-password"
```

**For PyPI publishing:**
```bash
export PYPI_TOKEN="your-pypi-token"
```

### Build Commands

```bash
# Build container image locally (default: Alpine)
dagger call build --source=.

# Build with specific base image
dagger call build --source=. --base-image="python:3.12-alpine"
dagger call build --source=. --base-image="cgr.dev/chainguard/python:latest-dev"
dagger call build --source=. --base-image="python:3.12-slim"

# Run tests (currently skipped until test suite exists)
dagger call test --source=.

# Build with custom settings
dagger call build-local \
  --source=. \
  --image-repository="riksarkivet/ra-mcp" \
  --base-image="python:3.12-alpine"
```

### Security: SBOM and Attestations

The project supports generating Software Bill of Materials (SBOM) and security scanning:

**Generate SBOM (Software Bill of Materials):**
```bash
# Generate SBOM in SPDX format (default)
dagger call generate-sbom-spdx --source=. --base-image="python:3.12-alpine"

# Generate SBOM in CycloneDX format
dagger call generate-sbom-cyclone-dx --source=. --base-image="python:3.12-alpine"

# Export SBOM to local file
dagger call export-sbom \
  --source=. \
  --base-image="python:3.12-alpine" \
  --format="spdx-json" \
  --output-path="./sbom.spdx.json"
```

**Vulnerability Scanning:**
```bash
# Scan for vulnerabilities (CRITICAL and HIGH)
dagger call scan-ci --source=.

# Scan with custom severity levels
dagger call scan --source=. --severity="CRITICAL,HIGH,MEDIUM" --format="table"

# Generate JSON scan report
dagger call scan-json --source=. --severity="CRITICAL,HIGH"

# Generate SARIF output for GitHub Security
dagger call scan-sarif --source=. --output-path="trivy-results.sarif"
```

**Important Notes:**
- **SBOM Generation**: Uses Trivy to scan the built container and generate SPDX or CycloneDX SBOMs
- **Provenance**: SLSA provenance is generated by BuildKit during the GitHub Actions publish workflow
- **GitHub Releases**: SBOMs and provenance are automatically generated and attached to releases as assets
- **Verification**: SBOMs can be used to verify container contents and detect supply chain issues
- **Format Support**: SPDX-JSON and CycloneDX-JSON formats are both supported

### Publishing to Docker Registry

The project supports multiple base images for different use cases:

**Supported Base Images:**
- `python:3.12-alpine` - Lightweight Alpine Linux (default)
- `cgr.dev/chainguard/python:latest-dev` - Wolfi-based Chainguard image (minimal CVEs)
- `cgr.dev/chainguard/python:latest` - Chainguard production image
- `python:3.12-slim` - Debian slim variant
- Any Python 3.12+ image with pip support

**Publishing Examples:**

```bash
# Publish Alpine variant with explicit tag
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.3.0" \
  --base-image="python:3.12-alpine" \
  --tag-suffix="-alpine" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.3.0-alpine

# Publish Wolfi/Chainguard variant
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.3.0" \
  --base-image="cgr.dev/chainguard/python:latest-dev" \
  --tag-suffix="-wolfi" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.3.0-wolfi

# Publish Debian slim variant
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.3.0" \
  --base-image="python:3.12-slim" \
  --tag-suffix="-slim" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.3.0-slim

# Auto-tag from pyproject.toml version (prefixes with "v")
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --base-image="python:3.12-alpine" \
  --tag-suffix="-alpine" \
  --source=.
```

**GitHub Actions Publishing:**

The publishing workflow ([publish.yml](.github/workflows/publish.yml)) uses `docker/build-push-action` for **native BuildKit attestation support**:

1. **Publishes container images with embedded attestations:**
   - Alpine: `riksarkivet/ra-mcp:v0.3.0-alpine`
   - Wolfi: `riksarkivet/ra-mcp:v0.3.0-wolfi`
   - **SBOM attestations** embedded in registry manifest
   - **SLSA Provenance** (mode=max) embedded in registry

2. **Also generates standalone SBOM files:**
   - `sbom-v0.3.0-alpine.spdx.json` (as release asset)
   - `sbom-v0.3.0-wolfi.spdx.json` (as release asset)

**Verify registry attestations:**
```bash
# Inspect SBOM in registry
docker buildx imagetools inspect riksarkivet/ra-mcp:v0.3.0-alpine --format "{{json .SBOM}}"

# Inspect provenance
docker buildx imagetools inspect riksarkivet/ra-mcp:v0.3.0-alpine --format "{{json .Provenance}}"

# Verify with Docker Scout
docker scout attestation riksarkivet/ra-mcp:v0.3.0-alpine
```

**Security Benefits:**
- Registry-native attestations (embedded in image manifest)
- SLSA Provenance Level 3 (build process transparency)
- SBOM attestations (dependency transparency)
- Multi-platform builds (amd64, arm64)
- Compliance ready (NTIA, EO 14028, SLSA)

### Publishing to PyPI

```bash
# Build and publish to PyPI
dagger call publish-pypi \
  --pypi-token=env:PYPI_TOKEN \
  --source=.
```

## Claude Code Integration

### Add MCP Server to Claude Code

```bash
# HTTP/SSE transport (recommended for development)
claude mcp add --transport sse ra-mcp http://localhost:8000/sse

# Verify connection
claude mcp list
```

### Claude Desktop Integration

Add to `claude_desktop_config.json`:

**macOS/Linux**: `~/.config/claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ra-mcp": {
      "command": "uv",
      "args": ["run", "ra", "serve"],
      "env": {}
    }
  }
}
```

## Coding Guidelines

### Core Principles

1. **Test-First Development**: Never write code without testing it! Always verify your changes work.
2. **Modify Over Create**: Prefer editing existing files over creating new ones.
3. **Read Completely**: Always read whole files, don't just read the head.
4. **Multiple Recommendations**: When possible, provide 2-3 alternative solutions.

### Documentation Standards

**When to use docstrings:**
- Public APIs and MCP tools
- Complex business logic
- Non-obvious behavior or algorithms
- Functions with important pre/post-conditions

**When to use better naming instead:**
- Simple, obvious functions
- Well-known patterns
- Standard operations

## API Endpoints

### Current Integrations
- **Search API**: `https://data.riksarkivet.se/api/records` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/Search-API)
- **IIIF Collections**: `https://lbiiif.riksarkivet.se/collection/arkiv` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/IIIF)
- **IIIF Images**: `https://lbiiif.riksarkivet.se`
- **ALTO XML**: `https://sok.riksarkivet.se/dokument/alto`
- **Bildvisning**: `https://sok.riksarkivet.se/bildvisning` (Interactive viewer)
- **OAI-PMH**: `https://oai-pmh.riksarkivet.se/OAI` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/OAI-PMH)

### Additional Resources
- **[Riksarkivet Data Platform Wiki](https://github.com/Riksarkivet/dataplattform/wiki)**: Comprehensive API documentation
- **[Förvaltningshistorik](https://forvaltningshistorik.riksarkivet.se/Index.htm)**: Semantic search interface (experimental)
- **[HTRflow](https://pypi.org/project/htrflow/)**: Handwritten text recognition pipeline (PyPI package)


## Common Tasks

### Adding a New MCP Tool

1. Create a new tool file in the appropriate MCP package (e.g., [search_tool.py](packages/search-mcp/src/search_mcp/search_tool.py))
2. Define a `register_*_tool(mcp)` function that uses `@mcp.tool()` decorator
3. Add detailed docstring with examples and parameter documentation
4. Call the register function from the package's [mcp.py](packages/search-mcp/src/search_mcp/mcp.py)

Example pattern (from [search_tool.py](packages/search-mcp/src/search_mcp/search_tool.py)):
```python
def register_search_tool(mcp: FastMCP):
    @mcp.tool()
    async def search_transcribed(keyword: str, offset: int, ...) -> str:
        """Tool description for LLM understanding."""
        ...
```

### Adding a New MCP Module

To add a new module (e.g., `ra-mcp-metadata`):

1. Create domain package: `packages/metadata/` with models, clients, operations
2. Create MCP package: `packages/metadata-mcp/` with tool registration
3. Optionally create CLI package: `packages/metadata-cli/`
4. Register in [server.py](src/ra_mcp_server/server.py) `AVAILABLE_MODULES`:

```python
from metadata_mcp.mcp import metadata_mcp

AVAILABLE_MODULES = {
    ...
    "metadata": {
        "server": metadata_mcp,
        "description": "Advanced metadata search and filtering",
        "default": False,
    },
}
```

5. Add dependencies to root `pyproject.toml`

### Adding API Clients

1. Create new client in the appropriate domain package (e.g., [packages/browse/src/ra_mcp_browse/clients/](packages/browse/src/ra_mcp_browse/clients/))
2. Follow existing patterns (see [alto_client.py](packages/browse/src/ra_mcp_browse/clients/alto_client.py))
3. Use the centralized HTTPClient from `ra_mcp_common.utils`
4. Add comprehensive error handling
5. Use dependency injection for HTTP client

### Adding a New MCP Resource

Resources provide static or dynamic content to MCP clients (see [guide_mcp/mcp.py](packages/guide-mcp/src/guide_mcp/mcp.py) for examples):

```python
@mcp.resource("riksarkivet://my-resource/{param}")
def get_my_resource(param: str) -> str:
    """Description of what this resource provides."""
    return f"Content for {param}"
```

### Updating Dependencies

```bash
# Add new dependency to a package
cd packages/common && uv add package-name

# Add development dependency (root)
uv add --dev package-name

# Update all dependencies
uv sync --upgrade

# Update specific dependency
uv add package-name@latest
```

### Working with Git

```bash
# Check status
git status

# Stage changes
git add .

# Commit with conventional commit format
git commit -m "feat: add new search feature"
git commit -m "fix: resolve timeout issue"
git commit -m "docs: update API documentation"

# Push changes
git push
```

**Conventional Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Releasing

Releases are automated via GitHub Actions. The workflow chain is:

```
git tag v0.X.Y && git push --tags
  → release.yml: generates changelog with git-cliff, creates GitHub Release
    → publish.yml: triggers on release:published, builds & pushes Docker images
```

**To cut a new release:**

```bash
# 1. Bump version in pyproject.toml
# 2. Commit the version bump
git commit -m "chore: bump version to 0.X.Y"

# 3. Tag and push
git tag v0.X.Y
git push && git push --tags
```

**How it works:**
- [release.yml](.github/workflows/release.yml) triggers on `v*` tag pushes
- Installs `git-cliff` and runs `git cliff --latest --strip header` to generate notes for the tagged version
- Creates a GitHub Release with those notes via `softprops/action-gh-release`
- Release notes include commit links back to GitHub (configured in [cliff.toml](cliff.toml))
- The existing [publish.yml](.github/workflows/publish.yml) triggers on `release: [published]` to build and push Docker images

**Local changelog generation:**
```bash
# Full changelog to CHANGELOG.md
make changelog

# Preview release notes for the latest tag
uvx git-cliff --latest --strip header
```

### Debugging Tips

**Environment Variables for Debugging:**
```bash
# Set logging level (DEBUG, INFO, WARNING, ERROR)
export RA_MCP_LOG_LEVEL=DEBUG

# Enable API call logging to file (ra_mcp_api.log)
export RA_MCP_LOG_API=1

# Override timeout (useful for Hugging Face)
export RA_MCP_TIMEOUT=120
```

**MCP Server Issues:**
```bash
# Use MCP Inspector for interactive testing
npx @modelcontextprotocol/inspector uv run ra serve

# Enable verbose logging with environment variable
RA_MCP_LOG_LEVEL=DEBUG uv run ra serve --port 8000

# Test HTTP endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

**Search Issues:**
```bash
# Test search directly via CLI with debug logging
RA_MCP_LOG_LEVEL=DEBUG uv run ra search "test query" --max 5

# Check API response
curl "https://data.riksarkivet.se/api/records?q=Stockholm&rows=1"

# Monitor API logs (if RA_MCP_LOG_API=1)
tail -f ra_mcp_api.log
```

## Observability & Telemetry

### Architecture

The project has a two-layer OpenTelemetry instrumentation strategy:

1. **FastMCP built-in instrumentation (automatic)**: FastMCP 3.0+ has native OTel support. It automatically creates spans for all `tools/call`, `resources/read`, `prompts/get`, and `delegate` operations with MCP semantic convention attributes. **Do NOT add manual spans to MCP tool handlers** — FastMCP already covers them.

2. **Manual instrumentation (project code)**: Domain operations, API clients, and the HTTP client have manual spans and metrics via `ra_mcp_common.telemetry.get_tracer()`.

### How it works

- OTel SDK is initialized only in the root package (`src/ra_mcp_server/telemetry.py`), gated on `RA_MCP_OTEL_ENABLED=true`
- All sub-packages use only `opentelemetry-api` (no-op when SDK absent)
- FastMCP uses the same global `TracerProvider`, so its automatic spans and project manual spans form a unified trace tree
- Module-level tracers: `get_tracer("ra_mcp.<component>")` from `ra_mcp_common.telemetry`

### Trace tree (MCP tool call)

```
tools/call search_transcribed          ← FastMCP (automatic)
└── delegate search_transcribed        ← FastMCP (composed server)
    └── tools/call search_transcribed  ← FastMCP (local provider)
        └── SearchOperations.search    ← manual span
            └── SearchAPI.search       ← manual span
                └── HTTP GET           ← manual span
```

### Environment variables

```bash
RA_MCP_OTEL_ENABLED=true              # Master switch (default: false)
OTEL_EXPORTER_OTLP_ENDPOINT=...       # Collector endpoint (default: http://localhost:4317)
OTEL_EXPORTER_OTLP_PROTOCOL=grpc      # grpc or http/protobuf (default: grpc)
OTEL_SERVICE_NAME=ra-mcp              # Service name (default: ra-mcp)
RA_MCP_OTEL_LOG_BRIDGE=true           # Bridge Python logging to OTel (default: true)
```

### What's instrumented manually

| Component | Tracer name | Spans | Metrics |
|-----------|-------------|-------|---------|
| HTTP client | `ra_mcp.http_client` | `HTTP GET` | request count, error count, duration, response size |
| Search API | `ra_mcp.search_api` | `SearchAPI.search` | — |
| Search ops | `ra_mcp.search_operations` | `SearchOperations.search` | — |
| Browse ops | `ra_mcp.browse_operations` | `browse_document`, `_fetch_page_contexts` | — |
| ALTO client | `ra_mcp.alto_client` | `ALTOClient.fetch_content` | — |
| IIIF client | `ra_mcp.iiif_client` | `IIIFClient.get_collection` | — |
| OAI-PMH client | `ra_mcp.oai_pmh_client` | `get_record`, `get_metadata`, `extract_manifest_id` | — |
| Search CLI | `ra_mcp.cli.search` | `cli.search` | — |
| Browse CLI | `ra_mcp.cli.browse` | `cli.browse` | — |

### Error recording pattern

Follow the HTTP client pattern (the gold standard in this codebase):

```python
except SomeError as e:
    span.set_status(StatusCode.ERROR, str(e))
    span.record_exception(e)
    self._error_counter.add(1, {"error.type": type(e).__name__})
    raise
```

### Verify telemetry

```bash
# Run full telemetry verification (starts Jaeger, exercises CLI, checks trace tree)
dagger call verify-telemetry --source=.
```

## MCP Specification Reference

For detailed information about the Model Context Protocol specification, implementation details, or when clarification is needed about MCP-specific features, refer to the official documentation:

- **[MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18)**: Official protocol specification
- **[FastMCP Documentation](https://github.com/jlowin/fastmcp)**: FastMCP library documentation

## Troubleshooting

### Common Issues

**Issue**: Server won't start
- Check if port 8000 is already in use: `lsof -i :8000`
- Try a different port: `uv run ra serve --port 8001`

**Issue**: No search results found
- Verify API is accessible: `curl https://data.riksarkivet.se/api/records`
- Check search syntax (use exact terms first, then wildcards)
- Try broader search terms

**Issue**: Import errors
- Reinstall dependencies: `uv sync --reinstall`
- Check Python version: `python --version` (requires 3.12+)

**Issue**: Tests not running
- Test infrastructure is being set up - see [Testing](#testing) section
- Dagger currently accepts zero tests as passing

### Getting Help

```bash
# General help
uv run ra --help

# Command-specific help
uv run ra serve --help
uv run ra search --help
uv run ra browse --help

# Check version
uv run ra --version
```

## Notes for Claude Code

When working with this codebase:

1. **Always test changes**: Run the server or CLI to verify functionality
2. **Read full context**: Use the Read tool on complete files, not just snippets
3. **Prefer modifications**: Edit existing code rather than creating new files
4. **Check types**: The project uses type hints - maintain them in all code
5. **Follow patterns**: Match existing code style and patterns (see [packages/search/src/ra_mcp_search/operations/](packages/search/src/ra_mcp_search/operations/))
6. **Document thoroughly**: MCP tools need excellent documentation for LLM understanding
7. **Workspace awareness**: Changes to common affect all packages; changes to search affect search-mcp and search-cli
8. **Layered architecture**: Domain logic lives in search/browse packages; MCP wrappers in *-mcp packages; CLI in *-cli packages

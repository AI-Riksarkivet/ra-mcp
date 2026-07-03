# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ra-mcp** (Riksarkivet Model Context Protocol) is an MCP server that provides access to transcribed historical documents from the Swedish National Archives (Riksarkivet).

### Architecture

The project is organized as a **uv workspace** with 44 packages under `packages/` plus a root server.
Packages are grouped by role into subfolders:

- `packages/libs/` — domain libraries (`*-lib`), plus `common`
- `packages/mcps/` — FastMCP servers (`*-mcp`) that wrap a domain library as MCP tools/resources
- `packages/cli/` — CLI (`search-cli`, `browse-cli`) and terminal-UI (`tui`) front-ends

```
ra-mcp/
├── src/ra_mcp_server/          # Root: Server composition and main CLI
│   ├── server.py               # FastMCP composition entry point + AVAILABLE_MODULES registry
│   └── cli/app.py              # Typer CLI root (ra command)
├── packages/
│   ├── libs/                   # domain libraries (*-lib) + common
│   │   ├── common/             # ra-mcp-common: Shared HTTP client, formatting, datasets, telemetry
│   │   ├── xml-lib/            # ra-mcp-xml: ALTOClient (ALTO XML parsing)
│   │   ├── iiif-lib/           # ra-mcp-iiif-lib: IIIFClient
│   │   ├── oai-pmh-lib/        # ra-mcp-oai-pmh-lib: OAIPMHClient
│   │   ├── search-lib/         # ra-mcp-search-lib: Search domain (models, client, operations)
│   │   ├── browse-lib/         # ra-mcp-browse-lib: Browse domain (models, operations, url_generator)
│   │   └── <dataset>-lib/      # 14 dataset libs (diplomatics, sbl, sjomanshus, filmcensur,
│   │                           #   rosenberg, court, aktiebolag, faltjagare, suffrage,
│   │                           #   specialsok, dds, wincars, sj, tora)
│   ├── mcps/                   # FastMCP servers wrapping the libs (*-mcp)
│   │   ├── search-mcp/         # ra-mcp-search-mcp: MCP tools for search
│   │   ├── browse-mcp/         # ra-mcp-browse-mcp: MCP tool for browse
│   │   ├── guide-mcp/          # ra-mcp-guide-mcp: MCP resources for historical guides
│   │   ├── htr-mcp/            # ra-mcp-htr-mcp: Handwritten text recognition (HTRflow)
│   │   ├── viewer-mcp/         # ra-mcp-viewer-mcp: Interactive document viewer (MCP App UI)
│   │   ├── pdf-mcp/            # ra-mcp-pdf-mcp: Interactive PDF viewer (MCP App UI)
│   │   ├── label-mcp/          # ra-mcp-label-mcp: Label Studio import (optional)
│   │   └── <dataset>-mcp/      # 14 dataset MCP servers (one per dataset lib above)
│   └── cli/                    # CLI + TUI front-ends
│       ├── search-cli/         # ra-mcp-search-cli: CLI command for search
│       ├── browse-cli/         # ra-mcp-browse-cli: CLI command for browse
│       └── tui/                # ra-mcp-tui: Interactive terminal browser
├── resources/                  # Historical guide markdown files
├── pyproject.toml              # Workspace configuration
└── uv.lock                     # Shared lockfile
```

### Package Structure

**ra-mcp-common** (no internal dependencies):
- [http_client.py](packages/libs/common/src/ra_mcp_common/http_client.py): Centralized httpx-based async HTTP client with logging
- [formatting.py](packages/libs/common/src/ra_mcp_common/formatting.py), [datasets.py](packages/libs/common/src/ra_mcp_common/datasets.py), [telemetry.py](packages/libs/common/src/ra_mcp_common/telemetry.py)

**Shared client libs** (depend on common): the ALTO/IIIF/OAI-PMH clients were extracted out of browse into their own packages so any package can reuse them:
- [ra-mcp-xml](packages/libs/xml-lib/src/ra_mcp_xml/client.py): `ALTOClient` (ALTO XML fetching + parsing)
- [ra-mcp-iiif-lib](packages/libs/iiif-lib/src/ra_mcp_iiif_lib/client.py): `IIIFClient`
- [ra-mcp-oai-pmh-lib](packages/libs/oai-pmh-lib/src/ra_mcp_oai_pmh_lib/client.py): `OAIPMHClient`

**ra-mcp-search-lib** (module `ra_mcp_search_lib`, depends on common):
- [config.py](packages/libs/search-lib/src/ra_mcp_search_lib/config.py): Search API URL and constants
- [models.py](packages/libs/search-lib/src/ra_mcp_search_lib/models.py): Pydantic models (SearchRecord, RecordsResponse, SearchResult)
- [search_client.py](packages/libs/search-lib/src/ra_mcp_search_lib/search_client.py): SearchClient client
- [search_operations.py](packages/libs/search-lib/src/ra_mcp_search_lib/search_operations.py): Search business logic

**ra-mcp-browse-lib** (module `ra_mcp_browse_lib`, depends on common + xml/iiif/oai-pmh libs):
- [config.py](packages/libs/browse-lib/src/ra_mcp_browse_lib/config.py): Browse API URLs and constants
- [models.py](packages/libs/browse-lib/src/ra_mcp_browse_lib/models.py): Pydantic models (BrowseResult, PageContext)
- [browse_operations.py](packages/libs/browse-lib/src/ra_mcp_browse_lib/browse_operations.py): Browse business logic (uses ALTOClient, IIIFClient, OAIPMHClient)
- [url_generator.py](packages/libs/browse-lib/src/ra_mcp_browse_lib/url_generator.py): URL construction helpers

**ra-mcp-search-mcp** (depends on search-lib + fastmcp):
- [tools.py](packages/mcps/search-mcp/src/ra_mcp_search_mcp/tools.py): FastMCP server setup, instructions, and tool registration
- [search_tool.py](packages/mcps/search-mcp/src/ra_mcp_search_mcp/search_tool.py): `search_transcribed` and `search_metadata` MCP tools
- [server.py](packages/mcps/search-mcp/src/ra_mcp_search_mcp/server.py): Standalone entry point for isolated dev/testing
- [formatter.py](packages/mcps/search-mcp/src/ra_mcp_search_mcp/formatter.py): Search result formatting for LLM output

**ra-mcp-browse-mcp** (depends on browse-lib + fastmcp):
- [tools.py](packages/mcps/browse-mcp/src/ra_mcp_browse_mcp/tools.py): FastMCP server setup, instructions, and tool registration
- [browse_tool.py](packages/mcps/browse-mcp/src/ra_mcp_browse_mcp/browse_tool.py): `browse_document` MCP tool
- [server.py](packages/mcps/browse-mcp/src/ra_mcp_browse_mcp/server.py): Standalone entry point for isolated dev/testing
- [formatter.py](packages/mcps/browse-mcp/src/ra_mcp_browse_mcp/formatter.py): Browse result formatting for LLM output

**ra-mcp-search-cli** (module `ra_mcp_search_cli`, depends on search-lib + typer + rich):
- [app.py](packages/cli/search-cli/src/ra_mcp_search_cli/app.py): Typer sub-app (`search_app`)
- [search_cmd.py](packages/cli/search-cli/src/ra_mcp_search_cli/search_cmd.py): `ra search` CLI command
- [formatter.py](packages/cli/search-cli/src/ra_mcp_search_cli/formatter.py): CLI output formatting

**ra-mcp-browse-cli** (module `ra_mcp_browse_cli`, depends on browse-lib + typer + rich):
- [app.py](packages/cli/browse-cli/src/ra_mcp_browse_cli/app.py): Typer sub-app (`browse_app`)
- [browse_cmd.py](packages/cli/browse-cli/src/ra_mcp_browse_cli/browse_cmd.py): `ra browse` CLI command
- [formatter.py](packages/cli/browse-cli/src/ra_mcp_browse_cli/formatter.py): CLI output formatting

**ra-mcp-tui** (module `ra_mcp_tui`): Textual-based interactive terminal browser (`tui_app`, `ra tui`).

**ra-mcp-guide-mcp** (depends on common + fastmcp):
- [tools.py](packages/mcps/guide-mcp/src/ra_mcp_guide_mcp/tools.py): FastMCP server and MCP resources for historical guides from `resources/`
- [server.py](packages/mcps/guide-mcp/src/ra_mcp_guide_mcp/server.py): Standalone entry point for isolated dev/testing

**Dataset / feature MCP modules**: `htr-mcp`, `viewer-mcp`, `pdf-mcp`, `label-mcp`, and 13 LanceDB-backed dataset modules (each a `<name>-lib` + `<name>-mcp` pair): diplomatics, sbl, sjomanshus, filmcensur, rosenberg, court, aktiebolag, faltjagare, suffrage, specialsok, dds, wincars, sj, plus `tora` geocoding. These follow the same lib/mcp split.

**Root package — ra-mcp** (depends on all always-on MCP packages; dataset + CLI packages are optional extras):
- [server.py](src/ra_mcp_server/server.py): FastMCP composition server with the `AVAILABLE_MODULES` registry (imports the always-on modules eagerly, optional modules via guarded `try`/`import`)
- [cli/app.py](src/ra_mcp_server/cli/app.py): Main Typer CLI entry point (`ra` command). Note it imports `search_app`, `browse_app`, and `tui_app` unconditionally, so the `ra` command requires the `cli` and `tui` extras to be installed.

### Package Dependencies

```
ra-mcp-common                              (no internal deps)
       ↑
ra-mcp-xml / iiif-lib / oai-pmh-lib        (depend on common)
ra-mcp-search-lib                          (depends on common)
ra-mcp-browse-lib                          (depends on common + xml/iiif/oai-pmh libs)
<dataset>-lib                              (depend on common)
       ↑
ra-mcp-search-mcp                          (depends on search-lib + fastmcp)
ra-mcp-browse-mcp                          (depends on browse-lib + fastmcp)
ra-mcp-guide-mcp / htr-mcp / viewer-mcp …  (depend on common/<dataset>-lib + fastmcp)
<dataset>-mcp                              (depend on <dataset>-lib + fastmcp)
ra-mcp-search-cli                          (depends on search-lib + typer + rich)
ra-mcp-browse-cli                          (depends on browse-lib + typer + rich)
ra-mcp-tui                                 (depends on search-lib/browse-lib + textual)
       ↑
ra-mcp (root)                              (composes the MCP modules; CLI/TUI/dataset packages are optional extras)
```

## Development Workflow

### Setup

```bash
# Clone repository
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp

# Install dependencies (syncs workspace packages)
uv sync

# Build the viewer-mcp and pdf-mcp App UIs (npm build of both UIs).
# Required before `ra serve`, or the MCP App UIs won't be built.
make build-ui
```

The `make serve` / `make serve-http` targets run `build-ui` automatically. If you launch the
server directly with `uv run ra serve`, run `make build-ui` yourself first.

### Running the Server

```bash
# MCP server (stdio) - for Claude Desktop integration
uv run ra serve

# MCP server (HTTP/SSE) - for web clients, testing, and development
uv run ra serve --port 7860

# With verbose logging
uv run ra serve --port 7860 --log
```

### Docker Compose (via Dagger)

Run the server using `.docker/docker-compose.yml` on the Dagger engine — no Docker daemon required.
Configuration mirrors the Helm chart ([charts/ra-mcp/values.yaml](charts/ra-mcp/values.yaml)).

```bash
# Start server (exposed on host port 7860)
dagger call compose-up up --ports 7860:7860
# or
make compose-up

# Run health check
dagger call compose-test
# or
make compose-test
```

**Connect to Claude Code:**

```bash
# 1. Start the server (keep this terminal running)
dagger call compose-up up --ports 7860:7860

# 2. In another terminal, add as MCP server
claude mcp add --transport http ra-mcp http://localhost:7860/mcp

# 3. Verify connection inside Claude Code
/mcp

# 4. Test with a search
# Ask Claude: "search for trolldom"
```

**Verify manually:**

```bash
# Health check
curl http://localhost:7860/health

# MCP endpoint (should return server info)
curl -X POST http://localhost:7860/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
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

```bash
# Run all tests
uv run pytest

# Run specific package tests
uv run pytest packages/libs/common/tests/ -v
uv run pytest packages/libs/search-lib/tests/ -v
uv run pytest packages/libs/browse-lib/tests/ -v

# Run with coverage
uv run pytest --cov=ra_mcp_common --cov=ra_mcp_search_lib --cov=ra_mcp_browse_lib --cov-report=html
```

### Testing Principles

Tests follow patterns drawn from httpx, pydantic, and FastMCP. Build bottom-up through the dependency stack:

```
Layer 0: ra-mcp-common               ← pure utilities, no internal deps
Layer 1: *-lib packages              ← domain models, clients, operations
         (xml, iiif-lib, oai-pmh-lib, search-lib, browse-lib, <dataset>-lib)
Layer 2: *-mcp, *-cli, tui packages  ← MCP tools, CLI commands, terminal UI
Layer 3: ra-mcp root server          ← composition
```

**Structure:**
- One test file per source module: `test_formatting.py` tests `formatting.py`
- Flat module-level functions — no test classes (httpx pattern)
- Each test file is self-contained with its own helpers and mock data
- Fixtures in `conftest.py` only for truly shared setup (e.g., mock HTTP response factory)
- XML/JSON fixture files in `packages/<pkg>/tests/fixtures/`

**Parametrize for edge cases** (pydantic pattern):
```python
@pytest.mark.parametrize("page_id,expected", [
    pytest.param("_00066", 66, id="standard"),
    pytest.param("_H0000459_00005", 5, id="compound"),
    pytest.param("_00000", 0, id="all-zeros"),
])
def test_page_id_to_number(page_id, expected):
    assert page_id_to_number(page_id) == expected
```

**Mock at the right boundary:**
- Domain libs (search-lib, browse-lib, the client libs): inject a mock `HTTPClient` via constructor — don't patch `httpx`
- MCP tool packages: use `Client(mcp)` for in-process testing, mock at the operations layer
- Never mock telemetry — test behavior, not instrumentation

**MCP tool testing** (FastMCP pattern):
```python
async def test_tool_returns_error_on_empty_keyword():
    async with Client(search_mcp) as client:
        result = await client.call_tool("transcribed", {"keyword": "", "offset": 0})
        assert "empty" in result.content[0].text.lower()
```

**Naming:** `test_<subject>_<scenario>` — e.g., `test_get_json_success`, `test_get_content_returns_none_on_404`

**What to test vs skip:**
- Test: behavior, return values, error handling, edge cases
- Skip: telemetry span attributes, log messages, `__init__.py` re-exports, config constants

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
uv run ra serve --port 7860
curl http://localhost:7860/mcp
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
dagger call build --source=. --base-image="python:3.13-alpine"
dagger call build --source=. --base-image="cgr.dev/chainguard/python:latest-dev"
dagger call build --source=. --base-image="python:3.13-slim"

# Run tests (currently skipped until test suite exists)
dagger call test --source=.

# Build with custom settings
dagger call build-local \
  --source=. \
  --image-repository="riksarkivet/ra-mcp" \
  --base-image="python:3.13-alpine"
```

### Security: SBOM and Attestations

The project supports generating Software Bill of Materials (SBOM) and security scanning:

**Generate SBOM (Software Bill of Materials):**
```bash
# Generate SBOM in SPDX format (default)
dagger call generate-sbom-spdx --source=. --base-image="python:3.13-alpine"

# Generate SBOM in CycloneDX format
dagger call generate-sbom-cyclone-dx --source=. --base-image="python:3.13-alpine"

# Export SBOM to local file
dagger call export-sbom \
  --source=. \
  --base-image="python:3.13-alpine" \
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
- `python:3.13-alpine` - Lightweight Alpine Linux (default)
- `cgr.dev/chainguard/python:latest-dev` - Wolfi-based Chainguard image (minimal CVEs)
- `cgr.dev/chainguard/python:latest` - Chainguard production image
- `python:3.13-slim` - Debian slim variant
- Any Python 3.13+ image with pip support

**Publishing Examples:**

```bash
# Publish Alpine variant with explicit tag
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.14.2" \
  --base-image="python:3.13-alpine" \
  --tag-suffix="-alpine" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.14.2-alpine

# Publish Wolfi/Chainguard variant
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.14.2" \
  --base-image="cgr.dev/chainguard/python:latest-dev" \
  --tag-suffix="-wolfi" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.14.2-wolfi

# Publish Debian slim variant
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.14.2" \
  --base-image="python:3.13-slim" \
  --tag-suffix="-slim" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.14.2-slim

# Auto-tag from pyproject.toml version (prefixes with "v")
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --base-image="python:3.13-alpine" \
  --tag-suffix="-alpine" \
  --source=.
```

**GitHub Actions Publishing:**

The publishing workflow ([publish.yml](.github/workflows/publish.yml)) uses `docker/build-push-action` for **native BuildKit attestation support**:

1. **Publishes container images with embedded attestations:**
   - Alpine: `riksarkivet/ra-mcp:v0.14.2-alpine`
   - Wolfi: `riksarkivet/ra-mcp:v0.14.2-wolfi`
   - **SBOM attestations** embedded in registry manifest
   - **SLSA Provenance** (mode=max) embedded in registry

2. **Also generates standalone SBOM files:**
   - `sbom-v0.14.2-alpine.spdx.json` (as release asset)
   - `sbom-v0.14.2-wolfi.spdx.json` (as release asset)

**Verify registry attestations:**
```bash
# Inspect SBOM in registry
docker buildx imagetools inspect riksarkivet/ra-mcp:v0.14.2-alpine --format "{{json .SBOM}}"

# Inspect provenance
docker buildx imagetools inspect riksarkivet/ra-mcp:v0.14.2-alpine --format "{{json .Provenance}}"

# Verify with Docker Scout
docker scout attestation riksarkivet/ra-mcp:v0.14.2-alpine
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
claude mcp add --transport sse ra-mcp http://localhost:7860/sse

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

### Live HTTP APIs (Riksarkivet)
The search/browse/viewer modules call these remote services directly:
- **Search API**: `https://data.riksarkivet.se/api/records` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/Search-API)
- **IIIF Collections**: `https://lbiiif.riksarkivet.se/collection/arkiv` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/IIIF)
- **IIIF Images**: `https://lbiiif.riksarkivet.se`
- **ALTO XML**: `https://sok.riksarkivet.se/dokument/alto`
- **Bildvisning**: `https://sok.riksarkivet.se/bildvisning` (Interactive viewer)
- **OAI-PMH**: `https://oai-pmh.riksarkivet.se/OAI` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/OAI-PMH)

### Local LanceDB dataset modules
In addition to the live HTTP APIs above, the server registers optional dataset modules that query
**local LanceDB indexes** (no remote API) rather than the Riksarkivet HTTP endpoints: diplomatics,
sbl, sjomanshus, filmcensur, rosenberg, court, aktiebolag, faltjagare, suffrage, specialsok, dds,
wincars, sj. Each ships as a `<name>-lib` (data access) + `<name>-mcp` (tools) pair and is registered
via a guarded `try`/`import` in `AVAILABLE_MODULES` (see [server.py](src/ra_mcp_server/server.py)), so a
missing `lancedb` wheel just skips the module instead of breaking startup.

### Additional Resources
- **[Riksarkivet Data Platform Wiki](https://github.com/Riksarkivet/dataplattform/wiki)**: Comprehensive API documentation
- **[Förvaltningshistorik](https://forvaltningshistorik.riksarkivet.se/Index.htm)**: Semantic search interface (experimental)
- **[HTRflow](https://pypi.org/project/htrflow/)**: Handwritten text recognition pipeline (PyPI package)


## Common Tasks

### Adding a New MCP Tool

1. Create a new tool file in the appropriate MCP package (e.g., [search_tool.py](packages/mcps/search-mcp/src/ra_mcp_search_mcp/search_tool.py))
2. Define a `register_*_tool(mcp)` function that uses `@mcp.tool()` decorator
3. Add detailed docstring with examples and parameter documentation
4. Call the register function from the package's [tools.py](packages/mcps/search-mcp/src/ra_mcp_search_mcp/tools.py)

Example pattern (from [search_tool.py](packages/mcps/search-mcp/src/ra_mcp_search_mcp/search_tool.py)):
```python
def register_search_tool(mcp: FastMCP):
    @mcp.tool()
    async def search_transcribed(keyword: str, offset: int, ...) -> str:
        """Tool description for LLM understanding."""
        ...
```

### Adding a New MCP Module

To add a new module (e.g., `ra-mcp-metadata`):

1. Create domain lib package: `packages/libs/metadata-lib/` (module `ra_mcp_metadata_lib`) with models, client, operations
2. Create MCP package: `packages/mcps/metadata-mcp/` (module `ra_mcp_metadata_mcp`) exposing a FastMCP server (e.g. `metadata_mcp`)
3. Register the workspace member + source mapping in the root [pyproject.toml](pyproject.toml):
   - add `ra-mcp-metadata-mcp` to `dependencies` (always-on) or to `[project.optional-dependencies]` as its own extra (optional)
   - add `ra-mcp-metadata-lib`/`ra-mcp-metadata-mcp` under `[tool.uv.sources]` and `known-first-party`
4. Register in [server.py](src/ra_mcp_server/server.py) `AVAILABLE_MODULES`.

   **Always-on modules** (search, browse, guide, htr, viewer, pdf) are imported eagerly at the top of
   the file and added to the `AVAILABLE_MODULES` dict literal:

   ```python
   from ra_mcp_metadata_mcp import metadata_mcp

   AVAILABLE_MODULES = {
       ...
       "metadata": {
           "server": metadata_mcp,
           "description": "Advanced metadata search and filtering",
           "default": True,
       },
   }
   ```

   **Optional modules** (label + the LanceDB datasets) follow the guarded `try`/`import` pattern so a
   missing optional dependency just skips the module instead of breaking startup:

   ```python
   try:
       from ra_mcp_metadata_mcp import metadata_mcp  # ty: ignore[unresolved-import]

       AVAILABLE_MODULES["metadata"] = {
           "server": metadata_mcp,
           "description": "Advanced metadata search and filtering",
           "default": True,
       }
   except ImportError:
       pass
   ```

   Optional notes: set `"no_namespace": True` to mount the module's tools without a namespace prefix
   (as viewer/pdf/sbl do).

5. Optionally add a CLI/TUI front-end and wire it into the relevant extra.

The server currently registers 21 modules: 6 always-on (search, browse, guide, htr, viewer, pdf) plus
15 optional (label, diplomatics, sbl, sjomanshus, filmcensur, rosenberg, court, aktiebolag, faltjagare,
suffrage, specialsok, dds, wincars, sj, tora).

### Adding API Clients

1. Create a new client lib package (the ALTO/IIIF/OAI-PMH clients each live in their own `*-lib` package)
2. Follow existing patterns (see [client.py](packages/libs/xml-lib/src/ra_mcp_xml/client.py) for `ALTOClient`, or [iiif-lib](packages/libs/iiif-lib/src/ra_mcp_iiif_lib/client.py) / [oai-pmh-lib](packages/libs/oai-pmh-lib/src/ra_mcp_oai_pmh_lib/client.py))
3. Use the centralized HTTPClient from `ra_mcp_common`
4. Add comprehensive error handling
5. Use dependency injection for HTTP client

### Adding a New MCP Resource

Resources provide static or dynamic content to MCP clients (see [guide_mcp/tools.py](packages/mcps/guide-mcp/src/ra_mcp_guide_mcp/tools.py) for examples):

```python
@mcp.resource("riksarkivet://my-resource/{param}")
def get_my_resource(param: str) -> str:
    """Description of what this resource provides."""
    return f"Content for {param}"
```

### Updating Dependencies

```bash
# Add new dependency to a package
cd packages/libs/common && uv add package-name

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
# One command: bumps pyproject.toml, commits, tags, and pushes
make release VERSION=0.5.0
```

This runs: `sed` version update → `git commit` → `git tag v0.5.0` → `git push && git push --tags`.

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
RA_MCP_LOG_LEVEL=DEBUG uv run ra serve --port 7860

# Test HTTP endpoint
curl -X POST http://localhost:7860/mcp \
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
            └── SearchClient.search    ← manual span
                └── HTTP GET           ← manual span
```

### Environment variables

```bash
RA_MCP_OTEL_ENABLED=true              # Master switch (default: false)
OTEL_EXPORTER_OTLP_ENDPOINT=...       # Collector endpoint (default: http://localhost:4317)
OTEL_EXPORTER_OTLP_PROTOCOL=grpc      # grpc or http/protobuf (default: grpc)
OTEL_SERVICE_NAME=ra-mcp              # Service name (default: ra-mcp)
ENVIRONMENT=production                # deployment.environment.name resource attr (optional)
RA_MCP_OTEL_LOG_BRIDGE=true           # Bridge Python logging to OTel (default: true)
```

### What's instrumented manually

| Component | Tracer name | Spans | Metrics |
|-----------|-------------|-------|---------|
| HTTP client | `ra_mcp.http_client` | `HTTP GET` | request count, error count, retry count, duration, response size |
| Search client | `ra_mcp.search.client` | `SearchClient.search` | — |
| Search ops | `ra_mcp.search_operations` | `SearchOperations.search` | request count (`ra_mcp.search.requests`), results per search (`ra_mcp.search.results`) |
| Browse ops | `ra_mcp.browse_operations` | `BrowseOperations.browse_document`, `BrowseOperations._fetch_page_contexts` | request count (`ra_mcp.browse.requests`), pages per browse (`ra_mcp.browse.pages`), empty pages (`ra_mcp.browse.empty_pages`) |
| ALTO client | `ra_mcp.alto_client` | `ALTOClient.fetch_content` | fetch count (`ra_mcp.alto.fetches`) |
| IIIF client | `ra_mcp.iiif_client` | `IIIFClient.get_collection`, `IIIFClient.fetch_manifest` | — |
| OAI-PMH client | `ra_mcp.oai_pmh_client` | `OAIPMHClient.get_metadata`, `OAIPMHClient.extract_manifest_id` | fetch count (`ra_mcp.oai_pmh.fetches`) |
| Viewer fetchers | fastmcp tracer (`fetchers.py`) | `fetch_image`, `fetch_thumbnail`, `fetch_text_layer` | — |
| Search CLI | `ra_mcp.cli.search` | `cli.search` | — |
| Browse CLI | `ra_mcp.cli.browse` | `cli.browse` | — |

### Error recording pattern

Follow the HTTP client pattern (the gold standard in this codebase). The OTel
Span Event API (`span.record_exception`) is being deprecated, so exception
detail is emitted as a structured log record via the shared
`record_span_exception(logger, exc)` helper (`ra_mcp_common.telemetry`) instead
of a span event. The span still carries `set_status(ERROR, ...)` — with the
error class in the message — and the log record (`exception.type` /
`exception.message` / `exception.stacktrace`) inherits the active `trace_id` /
`span_id` through the OTLP log bridge:

```python
from ra_mcp_common.telemetry import record_span_exception

except SomeError as e:
    span.set_status(StatusCode.ERROR, f"{type(e).__name__}: {e}")
    record_span_exception(logger, e)
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
- Check if port 7860 is already in use: `lsof -i :7860`
- Try a different port: `uv run ra serve --port 8001`

**Issue**: No search results found
- Verify API is accessible: `curl https://data.riksarkivet.se/api/records`
- Check search syntax (use exact terms first, then wildcards)
- Try broader search terms

**Issue**: Import errors
- Reinstall dependencies: `uv sync --reinstall`
- Check Python version: `python --version` (requires 3.13+)

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
5. **Follow patterns**: Match existing code style and patterns (see [packages/libs/search-lib/src/ra_mcp_search_lib/](packages/libs/search-lib/src/ra_mcp_search_lib/))
6. **Document thoroughly**: MCP tools need excellent documentation for LLM understanding
7. **Workspace awareness**: Changes to common affect all packages; changes to search-lib affect search-mcp, search-cli, and the TUI
8. **Layered architecture**: Domain logic lives in `*-lib` packages; MCP wrappers in `*-mcp` packages; CLI in `*-cli` packages and the TUI in `tui`

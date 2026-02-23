---
icon: lucide/code
---

# Development

Guide for setting up, contributing to, and deploying ra-mcp.

---

## Setup

```bash
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp
uv sync
```

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

## Running the Server

```bash
# MCP server (stdio) — for Claude Desktop integration
uv run ra serve

# MCP server (HTTP) — for web clients, testing, and development
uv run ra serve --port 7860

# With verbose logging
uv run ra serve --port 7860 -v

# Selective modules
uv run ra serve --port 7860 --modules search,browse
```

## Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run ra serve
```

## Testing

```bash
# Run all tests
uv run pytest

# Run specific package tests
uv run pytest packages/common/tests/ -v
uv run pytest packages/search/tests/ -v
uv run pytest packages/browse/tests/ -v

# Run with coverage
uv run pytest --cov=ra_mcp_common --cov=ra_mcp_search --cov=ra_mcp_browse --cov-report=html
```

### Testing Principles

- One test file per source module: `test_formatting.py` tests `formatting.py`
- Flat module-level functions — no test classes
- Parametrize for edge cases (pydantic pattern)
- Mock at the right boundary: inject a mock `HTTPClient` via constructor for domain packages, use `Client(mcp)` for MCP tools
- Test behavior, not instrumentation

## Code Quality

```bash
# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check --fix .

# Type check
uv run ty check
```

## CI Checks

Run the same checks as GitHub Actions locally:

```bash
# Full pipeline
dagger call checks && dagger call test

# Or via Makefile
make check
```

Always run `dagger call checks` before committing.

## Environment Variables

### Debugging

| Variable | Default | Description |
|----------|---------|-------------|
| `RA_MCP_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `RA_MCP_LOG_API` | *(unset)* | Enable API logging to `ra_mcp_api.log` |
| `RA_MCP_TIMEOUT` | `60` | Override default HTTP timeout in seconds |

### HTR

| Variable | Default | Description |
|----------|---------|-------------|
| `HTR_SPACE_URL` | `https://riksarkivet-htr-demo.hf.space` | Gradio Space URL |
| `HTR_TIMEOUT` | `300` | Transcription timeout in seconds |

## Adding a New MCP Tool

1. Create a tool file in the appropriate MCP package (e.g., `packages/search-mcp/src/ra_mcp_search_mcp/`)
2. Define a `register_*_tool(mcp)` function using `@mcp.tool()`
3. Add parameter documentation via `Annotated[type, Field(description=...)]`
4. Call the register function from the package's `tools.py`
5. Add tests using `Client(mcp)` for in-process testing

## Adding a New Module

1. Create domain package: `packages/mymodule/` with models, clients, operations
2. Create MCP package: `packages/mymodule-mcp/` with tool registration
3. Register in `src/ra_mcp_server/server.py` `AVAILABLE_MODULES`:

```python
AVAILABLE_MODULES = {
    "mymodule": {
        "server": mymodule_mcp,
        "description": "Description for --list-modules",
        "default": True,
    },
}
```

4. Add dependencies to root `pyproject.toml`

## Adding a New Skill

1. Create `plugins/ra-mcp-tools/skills/{name}/SKILL.md`
2. Add YAML frontmatter with `name` and `description`
3. The skill is auto-discovered on server restart

## Updating Dependencies

```bash
# Add to a package
cd packages/common && uv add package-name

# Add dev dependency (root)
uv add --dev package-name

# Sync all
uv sync
```

---

## Deployment

ra-mcp can be deployed as a Docker container, via Helm, or on Hugging Face Spaces.

### Docker

```bash
docker run -p 7860:7860 riksarkivet/ra-mcp:latest
```

Available image variants:

| Tag suffix | Base image | Notes |
|------------|-----------|-------|
| `-alpine` | `python:3.13-alpine` | Lightweight (default) |
| `-wolfi` | `cgr.dev/chainguard/python:latest-dev` | Minimal CVEs |
| `-slim` | `python:3.13-slim` | Debian slim |

### Docker Compose (via Dagger)

```bash
# Start server (exposed on host port 7860)
dagger call compose-up up --ports 7860:7860

# Run health check
dagger call compose-test
```

### Connect to Claude Code

```bash
# 1. Start the server
dagger call compose-up up --ports 7860:7860

# 2. Add as MCP server
claude mcp add --transport http ra-mcp http://localhost:7860/mcp

# 3. Verify
/mcp
```

### Helm

```bash
helm install ra-mcp charts/ra-mcp \
  --set image.tag=v0.8.0-alpine \
  --set opentelemetry.enabled=true
```

See [charts/ra-mcp/](https://github.com/AI-Riksarkivet/ra-mcp/tree/main/charts/ra-mcp) for the full values reference (autoscaling, ingress, PDB, security contexts).

### Hugging Face Spaces

The hosted instance runs at:

```
https://riksarkivet-ra-mcp.hf.space/mcp
```

### Health Endpoints

Available when running with HTTP transport:

| Endpoint | Purpose |
|----------|---------|
| `/health` | Liveness — always returns `{"status": "ok"}` |
| `/ready` | Readiness — returns mounted modules or 503 if none loaded |

```bash
curl http://localhost:7860/health
curl http://localhost:7860/ready
```

### Observability

Telemetry is gated on `RA_MCP_OTEL_ENABLED=true`. When enabled, traces, metrics, and logs are exported via OTLP.

#### Telemetry Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RA_MCP_OTEL_ENABLED` | `false` | Master switch |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Collector endpoint |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc` | `grpc` or `http/protobuf` |
| `OTEL_SERVICE_NAME` | `ra-mcp` | Service name |
| `RA_MCP_OTEL_LOG_BRIDGE` | `true` | Bridge Python logging to OTel |

#### Trace Tree

Every MCP tool call produces a trace spanning from the protocol layer down to HTTP:

``` mermaid
graph TD
  A["tools/call search_transcribed\n<i>FastMCP — automatic</i>"]
  B["delegate search_transcribed\n<i>FastMCP — composed server</i>"]
  C["tools/call search_transcribed\n<i>FastMCP — provider</i>"]
  D["SearchOperations.search\n<i>domain layer</i>"]
  E["SearchAPI.search\n<i>API client</i>"]
  F["HTTP GET\n<i>HTTP client</i>"]

  A --> B --> C --> D --> E --> F
```

#### Instrumented Components

| Component | Tracer name | Spans | Metrics |
|-----------|-------------|-------|---------|
| HTTP client | `ra_mcp.http_client` | `HTTP GET` | request count, error count, duration, response size |
| Search API | `ra_mcp.search_api` | `SearchAPI.search` | — |
| Search ops | `ra_mcp.search_operations` | `SearchOperations.search` | — |
| Browse ops | `ra_mcp.browse_operations` | `browse_document`, `_fetch_page_contexts` | — |
| ALTO client | `ra_mcp.alto_client` | `ALTOClient.fetch_content` | — |
| IIIF client | `ra_mcp.iiif_client` | `IIIFClient.get_collection` | — |
| OAI-PMH client | `ra_mcp.oai_pmh_client` | `get_record`, `get_metadata` | — |
| CLI commands | `ra_mcp.cli.*` | `cli.search`, `cli.browse` | — |

FastMCP adds automatic spans for all `tools/call` and `resources/read` operations.

#### Verify Telemetry

```bash
# Start Jaeger, exercise tools, check trace tree
dagger call verify-telemetry --source=.
```

### Security

#### SBOM

```bash
# SPDX format
dagger call generate-sbom-spdx --source=.

# CycloneDX format
dagger call generate-sbom-cyclone-dx --source=.
```

#### Vulnerability Scanning

```bash
# Scan for CRITICAL and HIGH
dagger call scan-ci --source=.

# Custom severity
dagger call scan --source=. --severity="CRITICAL,HIGH,MEDIUM" --format="table"
```

#### Supply Chain

- **SLSA Provenance** (Level 2) — generated by BuildKit during CI
- **Sigstore** — container images are signed
- **SBOM attestations** — embedded in registry manifests
- **OpenSSF Scorecard** — continuous security assessment

### Releasing

```bash
# Bump version, commit, tag, push
make release VERSION=0.9.0
```

This triggers:

1. `release.yml` — generates changelog with git-cliff, creates GitHub Release
2. `publish.yml` — builds and pushes Docker images (Alpine + Wolfi variants)

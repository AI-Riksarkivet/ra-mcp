<div align="center">
  <img src="assets/logo-rm-bg.png" alt="RA-MCP Logo" width="350">
</div>


# ra-mcp

[![Tests](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/ci.yml)
[![CodeQL](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/codeql.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/codeql.yml)
[![Publish](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/publish.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/publish.yml)
[![Secret Leaks](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/trufflehog.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/trufflehog.yml)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Docker Pulls](https://img.shields.io/docker/pulls/riksarkivet/ra-mcp)](https://hub.docker.com/r/riksarkivet/ra-mcp)

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/AI-Riksarkivet/ra-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/AI-Riksarkivet/ra-mcp)
[![SLSA 2](https://img.shields.io/badge/SLSA-Level%202-blue?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMyA3VjEyQzMgMTYuNTUgNi44NCAxOS43NCAxMiAyMUMxNy4xNiAxOS43NCAyMSAxNi41NSAyMSAxMlY3TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://slsa.dev/spec/v1.0/levels#build-l2)
[![Signed with Sigstore](https://img.shields.io/badge/Sigstore-Signed-purple?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMyA3VjEyQzMgMTYuNTUgNi44NCAxOS43NCAxMiAyMUMxNy4xNiAxOS43NCAyMSAxNi41NSAyMSAxMlY3TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://www.sigstore.dev/)
[![SBOM](https://img.shields.io/badge/SBOM-SPDX%202.3-green)](https://github.com/AI-Riksarkivet/ra-mcp/releases/latest)

A [Model Context Protocol](https://modelcontextprotocol.io/) server and CLI for searching and browsing transcribed historical documents from the Swedish National Archives (Riksarkivet). Provides full-text search across millions of AI-transcribed pages, complete page transcriptions, high-resolution IIIF image access, and archival research guides — all as MCP tools that any LLM client can use.

## Quick Start (MCP)

**Streamable HTTP** — works with ChatGPT, Claude, and any MCP-compatible client:

```
https://riksarkivet-ra-mcp.hf.space/mcp
```

**Claude Code:**

```bash
claude mcp add --transport http ra-mcp https://riksarkivet-ra-mcp.hf.space/mcp
```

**IDE (mcp.json):**

```json
{
  "mcpServers": {
    "ra-mcp": {
      "type": "streamable-http",
      "url": "https://riksarkivet-ra-mcp.hf.space/mcp"
    }
  }
}
```

## Quick Start (CLI)

```bash
uv pip install ra-mcp
```

```bash
# Search transcribed documents
ra search "trolldom"
ra search "((Stockholm OR Göteborg) AND troll*)"

# Browse specific pages
ra browse "SE/RA/310187/1" --pages "7,8,52" --search-term "trolldom"
```

See [packages/search-cli](packages/search-cli/) and [packages/browse-cli](packages/browse-cli/) for full syntax and search operators.

## Architecture

The project is a **uv workspace** with eight modular packages plus a root server:

| Package | Purpose | README |
|---------|---------|--------|
| **ra-mcp** (root) | Server composition and Typer CLI entry point | — |
| **ra-mcp-common** | Shared HTTP client, telemetry helpers | [README](packages/common/README.md) |
| **ra-mcp-search** | Search domain: models, API client, operations | [README](packages/search/README.md) |
| **ra-mcp-browse** | Browse domain: models, ALTO/IIIF/OAI-PMH clients | [README](packages/browse/README.md) |
| **ra-mcp-search-mcp** | MCP tools: `search_transcribed`, `search_metadata` | [README](packages/search-mcp/README.md) |
| **ra-mcp-browse-mcp** | MCP tool: `browse_document` | [README](packages/browse-mcp/README.md) |
| **ra-mcp-search-cli** | CLI command: `ra search` | [README](packages/search-cli/README.md) |
| **ra-mcp-browse-cli** | CLI command: `ra browse` | [README](packages/browse-cli/README.md) |
| **ra-mcp-guide-mcp** | MCP resources: archival research guides | [README](packages/guide-mcp/README.md) |

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

## Deployment

**Docker:**

```bash
docker run -p 7860:7860 riksarkivet/ra-mcp:latest
```

**Helm:**

```bash
helm install ra-mcp charts/ra-mcp \
  --set image.tag=v0.4.2-alpine \
  --set opentelemetry.enabled=true
```

See [charts/ra-mcp/](charts/ra-mcp/) for the full values reference (autoscaling, ingress, PDB, security contexts, etc.).

**Health endpoints** (available when running with HTTP transport):

| Endpoint | Purpose |
|----------|---------|
| `/health` | Liveness — always returns `{"status": "ok"}` |
| `/ready` | Readiness — returns mounted modules or 503 if none loaded |

## Observability

Telemetry is gated on a single environment variable. When enabled, traces, metrics, and logs are exported via OTLP.

| Variable | Default | Description |
|----------|---------|-------------|
| `RA_MCP_OTEL_ENABLED` | `false` | Master switch |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Collector endpoint |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc` | `grpc` or `http/protobuf` |
| `OTEL_SERVICE_NAME` | `ra-mcp` | Service name |
| `RA_MCP_OTEL_LOG_BRIDGE` | `true` | Bridge Python logging to OTel |

Instrumented components: HTTP client (spans + request/error/duration/size metrics), search and browse operations, ALTO/IIIF/OAI-PMH clients, and CLI commands. FastMCP adds automatic spans for all `tools/call` and `resources/read` operations.

## Development

```bash
git clone https://github.com/AI-Riksarkivet/ra-mcp.git && cd ra-mcp
uv sync

# Run code quality checks (format + lint + typecheck)
make check

# Or via Dagger (same as CI)
dagger call checks

# Start HTTP server for local development
uv run ra serve --port 8000

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run ra serve
```

## APIs & Data Sources

| API | Endpoint | Documentation |
|-----|----------|---------------|
| Search API | `https://data.riksarkivet.se/api/records` | [Wiki](https://github.com/Riksarkivet/dataplattform/wiki/Search-API) |
| IIIF Collections | `https://lbiiif.riksarkivet.se/collection/arkiv` | [Wiki](https://github.com/Riksarkivet/dataplattform/wiki/IIIF) |
| IIIF Images | `https://lbiiif.riksarkivet.se` | — |
| ALTO XML | `https://sok.riksarkivet.se/dokument/alto` | — |
| Bildvisning | `https://sok.riksarkivet.se/bildvisning` | — |
| OAI-PMH | `https://oai-pmh.riksarkivet.se/OAI` | [Wiki](https://github.com/Riksarkivet/dataplattform/wiki/OAI-PMH) |

Additional resources: [Riksarkivet Data Platform Wiki](https://github.com/Riksarkivet/dataplattform/wiki), [Förvaltningshistorik](https://forvaltningshistorik.riksarkivet.se/Index.htm) (semantic search, experimental), [HTRflow](https://pypi.org/project/htrflow/) (handwritten text recognition).

## License

[Apache 2.0](LICENSE)

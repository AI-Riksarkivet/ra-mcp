<div align="center">
  <img src="https://raw.githubusercontent.com/AI-Riksarkivet/ra-mcp/main/docs/assets/logo-rm-bg.png" alt="RA-MCP Logo" width="350">
</div>


# ra-mcp

[![Tests](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/ci.yml)
[![CodeQL](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/codeql.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/codeql.yml)
[![Publish](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/publish.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/publish.yml)
[![Secret Leaks](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/trufflehog.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/trufflehog.yml)

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Docker Pulls](https://img.shields.io/docker/pulls/riksarkivet/ra-mcp)](https://hub.docker.com/r/riksarkivet/ra-mcp)

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/AI-Riksarkivet/ra-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/AI-Riksarkivet/ra-mcp)
[![SLSA 2](https://img.shields.io/badge/SLSA-Level%202-blue?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMyA3VjEyQzMgMTYuNTUgNi44NCAxOS43NCAxMiAyMUMxNy4xNiAxOS43NCAyMSAxNi41NSAyMSAxMlY3TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://slsa.dev/spec/v1.0/levels#build-l2)
[![Signed with Sigstore](https://img.shields.io/badge/Sigstore-Signed-purple?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMyA3VjEyQzMgMTYuNTUgNi44NCAxOS43NCAxMiAyMUMxNy4xNiAxOS43NCAyMSAxNi41NSAyMSAxMlY3TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://www.sigstore.dev/)
[![SBOM](https://img.shields.io/badge/SBOM-SPDX%202.3-green)](https://github.com/AI-Riksarkivet/ra-mcp/releases/latest)

A [Model Context Protocol](https://modelcontextprotocol.io/) server and CLI for searching and browsing transcribed historical documents from the Swedish National Archives (Riksarkivet). Provides full-text search across millions of AI-transcribed pages, complete page transcriptions, handwritten text recognition, interactive document viewing, and archival research guides — all as MCP tools that any LLM client can use.

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

# Interactive terminal browser
ra tui "trolldom"
```

## Documentation

For architecture, development setup, deployment, tool reference, CLI reference, and more:

**[ai-riksarkivet.github.io/ra-mcp](https://ai-riksarkivet.github.io/ra-mcp/)**

## License

[Apache 2.0](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/LICENSE)

---
icon: lucide/layers
---

# Architecture

ra-mcp is organized as a **uv workspace** with modular packages, each with a single responsibility.

---

## Package Overview

| Package | Layer | Purpose |
|---------|-------|---------|
| **ra-mcp-common** | 0 | Shared HTTP client, telemetry helpers, formatting utilities |
| **ra-mcp-search** | 1 | Search domain: Pydantic models, API client, operations |
| **ra-mcp-browse** | 1 | Browse domain: models, ALTO/IIIF/OAI-PMH clients, operations |
| **ra-mcp-search-mcp** | 2 | MCP tools: `search_transcribed`, `search_metadata` |
| **ra-mcp-browse-mcp** | 2 | MCP tool: `browse_document` |
| **ra-mcp-guide-mcp** | 2 | MCP resources: archival research guides (50+ sections) |
| **ra-mcp-htr-mcp** | 2 | MCP tool: `htr_transcribe` (handwritten text recognition) |
| **ra-mcp-viewer-mcp** | 2 | MCP App: interactive document viewer with zoomable images |
| **ra-mcp-search-cli** | 2 | CLI command: `ra search` |
| **ra-mcp-browse-cli** | 2 | CLI command: `ra browse` |
| **ra-mcp-tui** | 2 | Interactive terminal browser: `ra tui` |
| **ra-mcp** (root) | 3 | Server composition + Typer CLI entry point |
| **ra-mcp-tools** (plugin) | — | Claude Code skills for research workflows |

## Dependency Graph

``` mermaid
graph TD
  common["ra-mcp-common\nshared HTTP client, telemetry"]

  search["ra-mcp-search\nsearch domain"]
  browse["ra-mcp-browse\nbrowse domain"]

  search_mcp["ra-mcp-search-mcp\nMCP tools"]
  search_cli["ra-mcp-search-cli\nCLI command"]
  browse_mcp["ra-mcp-browse-mcp\nMCP tool"]
  browse_cli["ra-mcp-browse-cli\nCLI command"]
  guide["ra-mcp-guide-mcp\nMCP resources"]
  htr["ra-mcp-htr-mcp\nHTR tool"]
  viewer["ra-mcp-viewer-mcp\nMCP App"]
  tui["ra-mcp-tui\nTerminal UI"]

  root["ra-mcp (root)\ncomposes all packages"]

  common --> search & browse & guide
  search --> search_mcp & search_cli & tui
  browse --> browse_mcp & browse_cli & tui
  search_mcp & search_cli & browse_mcp & browse_cli & guide & htr & viewer & tui --> root
```

## Layer Architecture

**Layer 0 — Foundation**

`ra-mcp-common` has no internal dependencies. It provides the `HTTPClient` (with retry, telemetry, and logging) used by all other packages.

**Layer 1 — Domain**

`ra-mcp-search` and `ra-mcp-browse` contain pure business logic: Pydantic models, API clients, and operations. No MCP or CLI dependency — they can be used as standalone Python libraries.

**Layer 2 — Interface**

Thin wrappers that expose domain logic through different interfaces:

- **MCP packages** (`*-mcp`) register tools/resources with FastMCP
- **CLI packages** (`*-cli`) register Typer commands with Rich output
- **TUI** (`ra-mcp-tui`) provides an interactive Textual application
- **HTR** (`ra-mcp-htr-mcp`) delegates to a remote Gradio Space
- **Viewer** (`ra-mcp-viewer-mcp`) is an MCP App serving an interactive HTML viewer

**Layer 3 — Composition**

The root package composes all MCP sub-servers into a single server using `FastMCP.add_provider()`. Each module gets a namespace (e.g., `search.transcribed`, `browse.document`) except the viewer which registers at root level.

## Module System

The root server has a registry of available modules:

| Module | Default | Tools / Resources |
|--------|---------|-------------------|
| `search` | Enabled | `search_transcribed`, `search_metadata` |
| `browse` | Enabled | `browse_document` |
| `guide` | Enabled | Historical research guides (MCP resources) |
| `htr` | Enabled | `htr_transcribe` |
| `viewer` | Enabled | `view-document`, `load-page`, `load-thumbnails` |

Modules can be selectively enabled:

```bash
ra serve --modules search,browse     # Only search and browse
ra serve --list-modules              # Show available modules
```

## Plugin System

The server discovers skills from `plugins/*/skills/` directories at startup using FastMCP's `SkillsDirectoryProvider`. Skills are SKILL.md files with YAML frontmatter that get exposed as MCP resources.

## Workspace Structure

```
ra-mcp/
├── src/ra_mcp_server/          # Root: Server composition, CLI, telemetry
├── packages/
│   ├── common/                 # Layer 0: HTTPClient, telemetry, formatting
│   ├── search/                 # Layer 1: Search domain
│   ├── browse/                 # Layer 1: Browse domain
│   ├── search-mcp/            # Layer 2: MCP tools for search
│   ├── browse-mcp/            # Layer 2: MCP tool for browse
│   ├── guide-mcp/             # Layer 2: MCP resources for guides
│   ├── htr-mcp/               # Layer 2: MCP tool for HTR
│   ├── viewer-mcp/            # Layer 2: MCP App for document viewing
│   ├── search-cli/            # Layer 2: CLI for search
│   ├── browse-cli/            # Layer 2: CLI for browse
│   └── tui/                   # Layer 2: Terminal UI
├── plugins/
│   └── ra-mcp-tools/          # Claude Code skills plugin
├── docs/                       # Documentation site (Zensical)
├── charts/ra-mcp/             # Helm chart
├── pyproject.toml             # Workspace root
└── uv.lock                    # Shared lockfile
```

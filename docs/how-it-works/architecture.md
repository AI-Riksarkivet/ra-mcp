# Architecture

ra-mcp is organized as a **uv workspace** with 44 packages under `packages/` plus a root server, each with a single responsibility. Packages are grouped by role into subfolders:

- `packages/libs/` — domain libraries (`*-lib`: Pydantic models, API clients, operations), plus `common`
- `packages/mcps/` — FastMCP servers (`*-mcp`) that wrap a domain library as MCP tools/resources
- `packages/cli/` — CLI (`search-cli`, `browse-cli`) and terminal-UI (`tui`) front-ends

The workspace targets Python 3.13+ and tracks the current releases of its core dependencies — FastMCP 3.4, LanceDB 0.34, OpenTelemetry 1.43, and Pydantic 2.13 on the Python side, and Vite 8, Svelte 5, and PDF.js 6 for the viewer / PDF MCP App UIs.

---

## Package Overview

### Foundation & domain libraries (Layer 0–1)

| Package | Layer | Purpose |
|---------|-------|---------|
| **ra-mcp-common** | 0 | Shared HTTP client, telemetry helpers, formatting, dataset utilities |
| **ra-mcp-xml** | 1 | `ALTOClient` — ALTO XML parsing (extracted from browse) |
| **ra-mcp-iiif-lib** | 1 | `IIIFClient` — IIIF collections & manifests (extracted from browse) |
| **ra-mcp-oai-pmh-lib** | 1 | `OAIPMHClient` — OAI-PMH metadata (extracted from browse) |
| **ra-mcp-search-lib** | 1 | Search domain: Pydantic models, API client, operations |
| **ra-mcp-browse-lib** | 1 | Browse domain: models, operations, URL generation |

### Core MCP & front-end packages (Layer 2)

| Package | Layer | Purpose |
|---------|-------|---------|
| **ra-mcp-search-mcp** | 2 | MCP tools: `search_transcribed`, `search_metadata` |
| **ra-mcp-browse-mcp** | 2 | MCP tool: `browse_document` |
| **ra-mcp-guide-mcp** | 2 | MCP resources: archival research guides |
| **ra-mcp-htr-mcp** | 2 | MCP tool: `htr_transcribe` (handwritten text recognition) |
| **ra-mcp-viewer-mcp** | 2 | MCP App: interactive document viewer with zoomable images |
| **ra-mcp-pdf-mcp** | 2 | MCP App: interactive PDF viewer (PDF.js, search, annotations) |
| **ra-mcp-label-mcp** | 2 | MCP tool: import pages to Label Studio for human annotation (optional) |
| **ra-mcp-search-cli** | 2 | CLI command: `ra search` |
| **ra-mcp-browse-cli** | 2 | CLI command: `ra browse` |
| **ra-mcp-tui** | 2 | Interactive terminal browser: `ra tui` |

### Dataset packages (Layer 1–2, optional)

Each dataset ships as a `*-lib` (LanceDB-backed query layer) plus a `*-mcp` (MCP tools). All are optional — they load only when `lancedb` is installed.

| Package pair | Dataset / tools |
|--------------|-----------------|
| **diplomatics-lib / -mcp** | SDHK medieval charters + MPO parchment fragments |
| **sbl-lib / -mcp** | Svenskt biografiskt lexikon (biographical articles) |
| **sjomanshus-lib / -mcp** | Seamen's house records (voyages, registrations) |
| **filmcensur-lib / -mcp** | Film censorship records 1911–2011 |
| **rosenberg-lib / -mcp** | Rosenberg's geographical lexicon |
| **court-lib / -mcp** | Court records (Domboksregister, Medelstad) |
| **aktiebolag-lib / -mcp** | Joint-stock company records |
| **faltjagare-lib / -mcp** | Jämtland field regiment soldiers |
| **suffrage-lib / -mcp** | Women's suffrage records |
| **specialsok-lib / -mcp** | Specialsök datasets (flygvapen, fångrullor, kurhuset, press, video) |
| **dds-lib / -mcp** | Church records (births, deaths, marriages) |
| **wincars-lib / -mcp** | Norrland vehicle registrations |
| **sj-lib / -mcp** | SJ railway properties & technical drawings |
| **tora-lib / -mcp** | TORA historical-place geocoding |

### Composition & plugin

| Package | Layer | Purpose |
|---------|-------|---------|
| **ra-mcp** (root) | 3 | Server composition + Typer CLI entry point |
| **ra-mcp-tools** (plugin) | — | Claude Code skills for research workflows |

## Dependency Graph

``` mermaid
graph TD
  common["ra-mcp-common\nshared HTTP client, telemetry"]

  clients["xml / iiif-lib / oai-pmh-lib\nALTO, IIIF, OAI-PMH clients"]
  search["ra-mcp-search-lib\nsearch domain"]
  browse["ra-mcp-browse-lib\nbrowse domain"]
  datasets["*-lib\n14 LanceDB dataset libraries"]

  search_mcp["ra-mcp-search-mcp"]
  browse_mcp["ra-mcp-browse-mcp"]
  guide["ra-mcp-guide-mcp"]
  htr["ra-mcp-htr-mcp"]
  viewer["ra-mcp-viewer-mcp\nMCP App"]
  pdf["ra-mcp-pdf-mcp\nMCP App"]
  dataset_mcp["*-mcp\ndataset MCP servers"]
  cli["search-cli / browse-cli / tui"]

  root["ra-mcp (root)\ncomposes all MCP packages"]

  common --> clients & search & browse & datasets & guide
  clients --> browse
  search --> search_mcp & cli
  browse --> browse_mcp & cli
  datasets --> dataset_mcp
  search_mcp & browse_mcp & guide & htr & viewer & pdf & dataset_mcp & cli --> root
```

## Layer Architecture

**Layer 0 — Foundation**

`ra-mcp-common` has no internal dependencies. It provides the `HTTPClient` (with retry, telemetry, and logging) plus shared formatting and dataset utilities used by all other packages.

**Layer 1 — Domain**

The domain libraries contain pure business logic — Pydantic models, API clients, and operations — with no MCP or CLI dependency, so they can be used as standalone Python libraries:

- `ra-mcp-search-lib` and `ra-mcp-browse-lib` cover full-text search and page browsing.
- The HTTP clients that used to live inside browse are now their own packages: **`ra-mcp-xml`** (`ALTOClient`), **`ra-mcp-iiif-lib`** (`IIIFClient`), and **`ra-mcp-oai-pmh-lib`** (`OAIPMHClient`). `browse-lib` depends on them.
- Each dataset has a `*-lib` package that queries a local LanceDB table.

**Layer 2 — Interface**

Thin wrappers that expose domain logic through different interfaces:

- **MCP packages** (`*-mcp`) register tools/resources with FastMCP
- **CLI packages** (`*-cli`) register Typer commands with Rich output
- **TUI** (`ra-mcp-tui`) provides an interactive Textual application
- **HTR** (`ra-mcp-htr-mcp`) delegates to a remote Gradio Space
- **Viewer** (`ra-mcp-viewer-mcp`) and **PDF** (`ra-mcp-pdf-mcp`) are MCP Apps serving interactive HTML UIs. Following the MCP Apps spec, the viewer delivers page and thumbnail images as size-bounded IIIF URLs (`/full/1500,/` and `/full/150,/`) that the browser fetches directly — declared in each app's `ResourceCSP` `resource_domains` — rather than proxying full-resolution scans as base64 through the tool-result channel

**Layer 3 — Composition**

The root package composes all enabled MCP sub-servers into a single server using `FastMCP.add_provider()`. Each module gets a namespace derived from the module name (e.g. tool `search_domboksregister` in the `court` module is exposed as `court:search_domboksregister`), except modules flagged `no_namespace` — currently **viewer**, **pdf**, and **sbl** — which register their tools at root level.

## Module System

The root server has a registry of available modules (`AVAILABLE_MODULES` in `src/ra_mcp_server/server.py`). All 21 modules are enabled by default. The optional dataset/annotation modules are wrapped in `try/except ImportError`, so they only register when their dependencies (e.g. `lancedb`, `label-studio-sdk`) are installed.

**Always-on core modules**

| Module | Namespaced | Tools / Resources |
|--------|------------|-------------------|
| `search` | `search:` | `search_transcribed`, `search_metadata` |
| `browse` | `browse:` | `browse_document` |
| `guide` | `guide:` | Historical research guides (MCP resources) |
| `htr` | `htr:` | `htr_transcribe` |
| `viewer` | root (no namespace) | `view_document`, `view_manifest`, `view_bild`, `load_page`, `load_thumbnails`, plus viewer-app controls |
| `pdf` | root (no namespace) | `display_pdf`, `search_pdf`, `list_pdfs`, `read_pdf_page`, plus pdf-app controls |

**Optional modules** (load when dependencies are present)

| Module | Namespaced | Tools |
|--------|------------|-------|
| `label` | `label:` | `import_to_label_studio` |
| `diplomatics` | `diplomatics:` | `search_sdhk`, `search_mpo`, `view_sdhk`, `view_mpo` |
| `sbl` | root (no namespace) | `search_sbl`, `view_sbl_article`, `load_sbl_article` |
| `sjomanshus` | `sjomanshus:` | `search_liggare`, `search_matrikel` |
| `filmcensur` | `filmcensur:` | `search_filmreg` |
| `rosenberg` | `rosenberg:` | `search_rosenberg` |
| `court` | `court:` | `search_domboksregister`, `search_medelstad` |
| `aktiebolag` | `aktiebolag:` | `search_bolag`, `search_styrelse` |
| `faltjagare` | `faltjagare:` | `search_faltjagare` |
| `suffrage` | `suffrage:` | `search_rostratt`, `search_fkpr` |
| `specialsok` | `specialsok:` | `search_flygvapen`, `search_fangrullor`, `search_kurhuset`, `search_press`, `search_video` |
| `dds` | `dds:` | `search_fodelse`, `search_doda`, `search_vigsel` |
| `wincars` | `wincars:` | `search_wincars` |
| `sj` | `sj:` | `search_juda`, `search_ritningar` |
| `tora` | `tora:` | `search_tora` |

Modules can be selectively enabled:

```bash
ra serve --modules search,browse     # Only search and browse
ra serve --list-modules              # Show available modules and exit
```

## Plugin System

The server discovers skills from `plugins/*/skills/` directories at startup using FastMCP's `SkillsDirectoryProvider`. Skills are SKILL.md files with YAML frontmatter that get exposed as MCP resources.

## Workspace Structure

```
ra-mcp/
├── src/ra_mcp_server/          # Root: Server composition, CLI, telemetry
│   └── server.py               # FastMCP composition + AVAILABLE_MODULES registry
├── packages/                   # 44 workspace packages, grouped by role
│   ├── libs/                   # domain libraries (*-lib) + common
│   │   ├── common/             # Layer 0: HTTPClient, telemetry, formatting, datasets
│   │   ├── xml-lib/            # Layer 1: ALTOClient (ALTO XML)
│   │   ├── iiif-lib/           # Layer 1: IIIFClient
│   │   ├── oai-pmh-lib/        # Layer 1: OAIPMHClient
│   │   ├── search-lib/         # Layer 1: Search domain
│   │   ├── browse-lib/         # Layer 1: Browse domain (depends on xml/iiif/oai)
│   │   └── <dataset>-lib/      # 14 optional LanceDB dataset libraries
│   ├── mcps/                   # FastMCP servers (*-mcp)
│   │   ├── search-mcp/         # Layer 2: MCP tools for search
│   │   ├── browse-mcp/         # Layer 2: MCP tool for browse
│   │   ├── guide-mcp/          # Layer 2: MCP resources for guides
│   │   ├── htr-mcp/            # Layer 2: MCP tool for HTR
│   │   ├── viewer-mcp/         # Layer 2: MCP App for document viewing
│   │   ├── pdf-mcp/            # Layer 2: MCP App for PDF viewing
│   │   ├── label-mcp/          # Layer 2: Label Studio import (optional)
│   │   └── <dataset>-mcp/      # 14 optional dataset MCP servers (diplomatics,
│   │                           #   sbl, sjomanshus, filmcensur, rosenberg, court,
│   │                           #   aktiebolag, faltjagare, suffrage, specialsok,
│   │                           #   dds, wincars, sj, tora)
│   └── cli/                    # CLI + TUI front-ends
│       ├── search-cli/         # Layer 2: CLI for search
│       ├── browse-cli/         # Layer 2: CLI for browse
│       └── tui/                # Layer 2: Terminal UI
├── plugins/
│   └── ra-mcp-tools/          # Claude Code skills plugin (8 skills)
├── resources/                  # Historical guide markdown files
├── docs/                       # Documentation site (Zensical)
├── charts/ra-mcp/             # Helm chart
├── pyproject.toml             # Workspace root
└── uv.lock                    # Shared lockfile
```

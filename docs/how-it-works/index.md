---
icon: lucide/cog
---

# How it Works

ra-mcp uses the [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) to give AI assistants direct access to the Swedish National Archives. Instead of the AI guessing about historical documents, it can search and read them in real time.

---

## What is MCP?

MCP is an open protocol that lets AI models call external tools. Think of it like a USB port for AI — any model that speaks MCP can plug into any MCP server and use its tools.

``` mermaid
graph LR
  A["AI Client\n(Claude, ChatGPT, etc)"] <-->|"MCP\ntool calls"| B["ra-mcp Server"]
  B --> C["Riksarkivet\nData Platform\n(Search, IIIF, ALTO, OAI-PMH)"]
  B --> D["HTRflow\nGradio Space\n(Handwritten text recognition)"]
```

When you ask Claude *"Find documents about trolldom"*, the AI:

1. Recognizes it needs to search historical archives
2. Calls the `search_transcribed` tool via MCP
3. ra-mcp queries the Riksarkivet Search API
4. Results come back through MCP to the AI
5. The AI presents them to you with context and analysis

## The Tools

### search_transcribed

Searches AI-transcribed text across millions of digitised historical document pages. Supports advanced Solr query syntax including wildcards, fuzzy matching, boolean operators, proximity searches, and date filtering.

**Example query flow:**

```
User: "Find 17th century court records mentioning trolldom near Stockholm"

AI calls: search_transcribed(
    keyword='("Stockholm trolldom"~10)',
    offset=0,
    year_min=1600,
    year_max=1699,
    sort="timeAsc"
)
```

### search_metadata

Searches document metadata fields — titles, personal names, place names, archival descriptions, and provenance. Covers 2M+ records. Useful for finding specific archives, people, or locations.

### browse_document

Retrieves complete page transcriptions from a specific document. Each result includes the full transcribed text and direct links to the original page images in Riksarkivet's image viewer.

### htr_transcribe

Transcribes handwritten document images using AI-powered handwritten text recognition (HTRflow). Accepts image URLs and returns an interactive viewer, per-page transcription data, and archival exports in ALTO XML, PAGE XML, or JSON. Supports Swedish, Norwegian, English, and medieval documents.

### view_document

Displays document pages in an interactive viewer with zoomable images and text layer overlays. The viewer runs directly inside the MCP host (Claude, ChatGPT) as an MCP App.

See [Tools & Skills](../tools/index.md) for full parameter documentation.

## Data Sources

ra-mcp connects to several Riksarkivet APIs:

| API | Endpoint | Purpose |
|-----|----------|---------|
| **Search API** | `data.riksarkivet.se/api/records` | Full-text search across transcribed documents |
| **ALTO XML** | `sok.riksarkivet.se/dokument/alto` | Structured page transcriptions with text coordinates |
| **IIIF** | `lbiiif.riksarkivet.se` | High-resolution document images and collection manifests |
| **OAI-PMH** | `oai-pmh.riksarkivet.se/OAI` | Document metadata and collection structure |
| **Bildvisaren** | `sok.riksarkivet.se/bildvisning` | Interactive image viewer (links provided in results) |

All data comes from the [Riksarkivet Data Platform](https://github.com/Riksarkivet/dataplattform/wiki), which hosts AI-transcribed materials from the Swedish National Archives.

Additional resources: [Förvaltningshistorik](https://forvaltningshistorik.riksarkivet.se/Index.htm) (semantic search, experimental), [HTRflow](https://pypi.org/project/htrflow/) (handwritten text recognition).

## Archive Coverage

The archive has three access tiers — not all materials are searchable the same way:

| Tier | Tool | Coverage |
|------|------|----------|
| **Metadata catalog** | `search_metadata` | 2M+ records — titles, names, places, dates |
| **Digitised images** | `browse_document` (links) | ~73M pages viewable via bildvisaren |
| **AI-transcribed text** | `search_transcribed` | ~1.6M pages — currently court records (hovrätt, trolldomskommissionen, poliskammare, magistrat) from 17th-18th centuries |

Church records, estate inventories, and military records are typically cataloged and often digitised, but NOT AI-transcribed.

### Transcription Quality

The AI-transcribed text was produced by HTR (Handwritten Text Recognition) and OCR models. These transcriptions are **not perfect** — they contain recognition errors including misread characters, merged or split words, and garbled passages, especially in older or damaged documents.

This has a direct impact on search: an exact search for `Stockholm` will miss documents where the transcription reads `Stockholn` or `Stookholm` due to recognition errors. **Always use fuzzy search (`~`)** to compensate — `stockholm~1` catches common misreads and significantly increases the number of hits.

## The Plugin Model

ra-mcp is one piece of a larger ecosystem. Multiple MCP servers can be connected to the same AI client:

``` mermaid
graph LR
  client["AI Client\n(Claude)"]
  client --> ramcp["ra-mcp\nSearch, browse, HTR, viewer, guides"]
  client --> htrflow["htrflow-mcp\nStandalone HTR\n(alternative)"]
  client --> other["other servers\nAny MCP-compatible tool"]
```

Together with external tools, they enable a complete research workflow: search the archives, read transcriptions, re-transcribe pages that need better OCR/HTR, and view original documents — all from within a single AI conversation.

---

## Architecture

ra-mcp is organized as a **uv workspace** with modular packages, each with a single responsibility.

### Package Overview

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

### Dependency Graph

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

### Layer Architecture

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

### Module System

The root server has a registry of available modules:

| Module | Default | Tools / Resources |
|--------|---------|-------------------|
| `search` | Enabled | `search_transcribed`, `search_metadata` |
| `browse` | Enabled | `browse_document` |
| `guide` | Enabled | Historical research guides (MCP resources) |
| `htr` | Enabled | `htr_transcribe` |
| `viewer` | Enabled | `view_document`, `load_page`, `load_thumbnails` |

Modules can be selectively enabled:

```bash
ra serve --modules search,browse     # Only search and browse
ra serve --list-modules              # Show available modules
```

### Plugin System

The server discovers skills from `plugins/*/skills/` directories at startup using FastMCP's `SkillsDirectoryProvider`. Skills are SKILL.md files with YAML frontmatter that get exposed as MCP resources.

### Workspace Structure

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

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
  A["AI Client\n(Claude, etc)"] <-->|"MCP\ntool calls"| B["ra-mcp Server"]
  B --> C["Riksarkivet\nData Platform\n(Search, IIIF, ALTO, OAI-PMH)"]
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

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `keyword` | Search query with Solr syntax |
| `offset` | Pagination starting position (0, 50, 100, ...) |
| `max_results` | Documents per page (default: 25) |
| `year_min` / `year_max` | Filter by date range |
| `sort` | `relevance`, `timeAsc`, `timeDesc` |

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

Searches document metadata fields — titles, personal names, place names, archival descriptions, and provenance. Useful for finding specific archives, people, or locations.

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `keyword` | General free-text search |
| `name` | Search by person name |
| `place` | Search by place name |
| `only_digitised` | Limit to digitised materials (default: true) |

### browse_document

Retrieves complete page transcriptions from a specific document. Each result includes the full transcribed text and direct links to the original page images in Riksarkivet's image viewer.

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `reference_code` | Document identifier (e.g., `SE/RA/420422/01`) |
| `pages` | Page specification: `"5"`, `"1-10"`, or `"5,7,9"` |
| `highlight_term` | Keyword to highlight in transcriptions |

## Architecture

ra-mcp is organized as a **uv workspace** with modular packages, each with a single responsibility:

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

  root["ra-mcp (root)\ncomposes all packages"]

  common --> search & browse & guide
  search --> search_mcp & search_cli
  browse --> browse_mcp & browse_cli
  search_mcp & search_cli & browse_mcp & browse_cli & guide --> root
```

**Why this structure?**

- **Domain packages** (search, browse) contain pure business logic with no MCP dependency
- **MCP packages** are thin wrappers that register tools with FastMCP
- **CLI packages** provide terminal access to the same operations
- The **root package** composes everything into a single server

This means you can use the search/browse logic independently, or run the full MCP server with all tools available.

## Data Sources

ra-mcp connects to several Riksarkivet APIs:

| API | Purpose |
|-----|---------|
| **Search API** | Full-text search across transcribed documents |
| **ALTO XML** | Structured page transcriptions with text coordinates |
| **IIIF** | High-resolution document images |
| **OAI-PMH** | Document metadata and collection structure |
| **Bildvisaren** | Interactive image viewer (links provided in results) |

All data comes from the [Riksarkivet Data Platform](https://github.com/Riksarkivet/dataplattform/wiki), which hosts AI-transcribed materials from the Swedish National Archives.

## The Plugin Model

ra-mcp is one piece of a larger ecosystem. Multiple MCP servers can be connected to the same AI client, each providing different capabilities:

``` mermaid
graph LR
  client["AI Client\n(Claude)"]
  client --> htrflow["htrflow-mcp\nHandwritten text recognition"]
  client --> ramcp["ra-mcp\nArchive search & browse"]
  client --> other["other servers\nAny MCP-compatible tool"]
```

**ra-mcp** provides:

- Search transcribed documents
- Browse page transcriptions
- Historical research guides

**htrflow-mcp** adds:

- Transcribe handwritten document images
- Process multi-page spreads
- Export in ALTO XML, PAGE XML, or JSON

Together, they enable a complete research workflow: search the archives, read transcriptions, and re-transcribe pages that need better OCR/HTR — all from within a single AI conversation.

See [Getting Started](../getting-started/index.md) for setup instructions.

## Server Module System

The ra-mcp server itself is modular. It composes several internal modules that can be enabled or disabled:

| Module | Tools / Resources | Default |
|--------|-------------------|---------|
| **search** | `search_transcribed`, `search_metadata` | Enabled |
| **browse** | `browse_document` | Enabled |
| **guide** | Historical research guides (MCP resources) | Enabled |

Each module is a self-contained FastMCP sub-server that gets composed into the main server at startup. This makes it straightforward to add new modules — for example, a future `metadata` module for advanced filtering, or an `image` module for direct IIIF image access.

## Observability

ra-mcp supports OpenTelemetry for tracing and metrics. When enabled, every tool call produces a trace spanning from the MCP protocol layer down through domain operations to individual HTTP requests:

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

Enable with:

```bash
export RA_MCP_OTEL_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

---
icon: lucide/archive
---

# ra-mcp

A [Model Context Protocol](https://modelcontextprotocol.io/) server and CLI for searching and browsing transcribed historical documents from the **Swedish National Archives** (Riksarkivet).

Provides full-text search across millions of AI-transcribed pages, complete page transcriptions, high-resolution IIIF image access, and archival research guides — all as MCP tools that any LLM client can use.

## Quick start (MCP)

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

## Quick start (CLI)

```bash
uv pip install ra-mcp
```

```bash
# Search transcribed documents
ra search "trolldom"
ra search "((Stockholm OR Goteborg) AND troll*)"

# Browse specific pages
ra browse "SE/RA/310187/1" --pages "7,8,52" --search-term "trolldom"
```

## Available tools

| Tool | Description |
|------|-------------|
| `search_transcribed` | Full-text search across AI-transcribed historical documents with advanced Solr query syntax |
| `search_metadata` | Search document metadata (titles, names, places, provenance) |
| `browse_document` | View complete page transcriptions by reference code with keyword highlighting |

## Search syntax

| Type | Syntax | Example |
|------|--------|---------|
| Exact | `"word"` | `"Stockholm"` |
| Wildcard | `*`, `?` | `"Stock*"`, `"St?ckholm"` |
| Fuzzy | `~N` | `"Stockholm~1"` |
| Proximity | `"w1 w2"~N` | `"Stockholm trolldom"~10` |
| Boolean | `AND`, `OR`, `NOT` | `(Stockholm AND trolldom)` |
| Grouping | `(...)` | `((Stockholm OR Goteborg) AND troll*)` |

## Architecture

The project is a **uv workspace** with eight modular packages:

```
ra-mcp-common              (shared HTTP client, telemetry)
       |
ra-mcp-search              (search domain)
ra-mcp-browse              (browse domain)
       |
ra-mcp-search-mcp          (MCP tools for search)
ra-mcp-browse-mcp          (MCP tool for browse)
ra-mcp-guide-mcp           (MCP resources for guides)
ra-mcp-search-cli          (CLI: ra search)
ra-mcp-browse-cli          (CLI: ra browse)
       |
ra-mcp (root)              (composes all packages)
```

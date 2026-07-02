# ra-mcp-diplomatics-mcp

MCP tools for SDHK and MPO medieval document search.

## Overview

Thin MCP wrapper around `ra-mcp-diplomatics-lib`. The composed server (`diplomatics_mcp` in `tools.py`) registers two FastMCP search tools — `search_sdhk` and `search_mpo` — backed by a lazily-opened LanceDB connection. The package also ships two viewer tools, `view_sdhk` and `view_mpo`, which open a single charter/fragment in the interactive document viewer (via `ra-mcp-viewer-mcp`); their register functions are present in the package but are not wired into `tools.py`. The dataset covers SDHK (Diplomatarium Suecanum) medieval Swedish charters and MPO (Medeltida Pergamentomslag) medieval parchment fragments.

Tools are registered as bare names and get namespaced as `diplomatics:<tool>` when composed into the root server.

## MCP Tools

### `search_sdhk`

Search SDHK (Diplomatarium Suecanum) — 44,000+ medieval Swedish charters dated before 1540 (about 15,000 digitized, with IIIF manifest URLs). Returns a markdown table with ID, date, place, author, summary, and status.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across SDHK charter text |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `author` | str \| None | None | Optional filter: charter author (case-insensitive substring match) |
| `place` | str \| None | None | Optional filter: charter place (case-insensitive substring match) |
| `language` | str \| None | None | Optional filter: charter language (case-insensitive substring match) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

### `search_mpo`

Search MPO (Medeltida Pergamentomslag) — 23,000+ medieval parchment fragments used as bookbinding covers, each with a IIIF manifest URL. Returns a markdown table with ID, category, dating, origin, script, and content.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across MPO fragment text |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `category` | str \| None | None | Optional filter: fragment category (case-insensitive substring match) |
| `institution` | str \| None | None | Optional filter: holding institution (case-insensitive substring match) |
| `script` | str \| None | None | Optional filter: script type (case-insensitive substring match) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

### `view_sdhk`

View a digitized SDHK charter in the document viewer with full metadata. Opens the interactive viewer with charter images and a metadata panel (author, date, summary, edition text, seal descriptions). Only works for digitized charters. *(Defined in `view_sdhk_tool.py`; not registered by `tools.py`.)*

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sdhk_id` | int | *(required)* | SDHK charter ID (e.g. 85, 28672) |
| `highlight_term` | str \| None | None | Optional search term to highlight |
| `max_pages` | int | 20 | Maximum pages to load (≤ 20) |

*(A FastMCP `ctx: Context` is injected automatically and is not a caller-supplied parameter.)*

### `view_mpo`

View an MPO parchment fragment in the document viewer with full codicological metadata (manuscript type, dating, script, material, content, decoration, damage). *(Defined in `view_mpo_tool.py`; not registered by `tools.py`.)*

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mpo_id` | int | *(required)* | MPO fragment ID (e.g. 1, 42) |
| `highlight_term` | str \| None | None | Optional search term to highlight |
| `max_pages` | int | 20 | Maximum pages to load (≤ 20) |

*(A FastMCP `ctx: Context` is injected automatically and is not a caller-supplied parameter.)*

## Components

- **tools.py**: FastMCP server (`diplomatics_mcp`) setup, instructions, and registration of the search tools
- **sdhk_tool.py**: `search_sdhk` tool registration and LanceDB connection handling
- **mpo_tool.py**: `search_mpo` tool registration and LanceDB connection handling
- **view_sdhk_tool.py**: `view_sdhk` viewer tool registration (opens a charter in the document viewer)
- **view_mpo_tool.py**: `view_mpo` viewer tool registration (opens a fragment in the document viewer)
- **formatter.py**: Formats SDHK/MPO results and record info for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, streamable-http on /mcp)
python -m ra_mcp_diplomatics_mcp.server --port 3003

# stdio transport
python -m ra_mcp_diplomatics_mcp.server --stdio
```

The default port is `3003` (overridable via the `PORT` environment variable or `--port`).

## Dependencies

- Internal: `ra-mcp-diplomatics-lib`, `ra-mcp-viewer-mcp`
- External: `fastmcp==3.4.2`

## Part of ra-mcp

Tools are registered as bare names and get namespaced as `diplomatics:<tool>` when composed into the root server via the `AVAILABLE_MODULES` registry. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

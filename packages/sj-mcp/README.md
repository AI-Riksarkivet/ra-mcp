# ra-mcp-sj-mcp

MCP tools for Swedish State Railways (SJ) records search.

## Overview

Thin MCP wrapper around `ra-mcp-sj-lib`. Registers two FastMCP tools — `search_juda` and `search_ritningar` — that run full-text search over a local LanceDB copy of the SJ railway property register (JUDA) and the FIRA/SIRA technical drawing registers. Tools are registered as bare names and get namespaced as `<module>:<tool>` when composed into the root server.

## MCP Tools

### `search_juda`

Search the SJ railway property register (JUDA) — railway properties managed by Swedish State Railways. Returns property description, county, municipality, owner, and notes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across JUDA railway property records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `fbagrkod2` | str \| None | None | Filter: owner code (case-insensitive substring match, e.g. `Jernhusen`) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

### `search_ritningar`

Search SJ railway technical drawings (FIRA/SIRA) of stations, buildings, and infrastructure. Returns station/building name, description, drawing number, date, format, district, and building type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across FIRA/SIRA railway drawing records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `dkod` | str \| None | None | Filter: district code (case-insensitive substring match) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

## Components

- **tools.py**: FastMCP server setup, instructions, and tool registration
- **juda_tool.py**: `search_juda` tool — registration, validation, lazy LanceDB connection
- **ritningar_tool.py**: `search_ritningar` tool — registration, validation, lazy LanceDB connection
- **formatter.py**: Formats JUDA and Ritningar search results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3015)
python -m ra_mcp_sj_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_sj_mcp.server --port 8080

# stdio transport
python -m ra_mcp_sj_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-sj-lib` (which depends on `ra-mcp-common`)
- External: `fastmcp`

## Part of ra-mcp

Composed into the root server alongside the other dataset modules. Tools are registered as bare names (`search_juda`, `search_ritningar`) and get namespaced as `<module>:<tool>` in the composed server. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

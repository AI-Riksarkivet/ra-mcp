# ra-mcp-sjomanshus-mcp

MCP tools for Swedish seamen's house records (Sjömanshus) search.

## Overview

Thin MCP wrapper around `ra-mcp-sjomanshus-lib`. Registers two FastMCP tools — `search_liggare` and `search_matrikel` — that run full-text search over a local LanceDB copy of the Swedish seamen's house records: voyage records (Liggare) and registration records (Matrikel) from the 1700s–1900s. Tools are registered as bare names and get namespaced as `<module>:<tool>` when composed into the root server.

## MCP Tools

### `search_liggare`

Search Swedish seamen's voyage records (Liggare). Returns seaman name, rank, ship, home port, destination, captain, and shipowner.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across Liggare voyage records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `befattning` | str \| None | None | Filter: occupation/rank (case-insensitive substring, e.g. `matros`, `styrman`) |
| `fartyg` | str \| None | None | Filter: ship name (case-insensitive substring) |
| `sjoemanshus` | str \| None | None | Filter: seamen's house name (case-insensitive substring, e.g. `Göteborg`) |
| `hemmahamn` | str \| None | None | Filter: home port (case-insensitive substring) |
| `kapten` | str \| None | None | Filter: captain name (case-insensitive substring) |
| `redare` | str \| None | None | Filter: shipowner name (case-insensitive substring) |
| `destination` | str \| None | None | Filter: voyage destination (case-insensitive substring, e.g. `Medelhavet`) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

### `search_matrikel`

Search Swedish seamen's registration records (Matrikel). Returns seaman name, birth info, parents, home parish, and registration/deregistration dates.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across Matrikel registration records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `sjoemanshus` | str \| None | None | Filter: seamen's house name (case-insensitive substring, e.g. `Göteborg`) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

## Components

- **tools.py**: FastMCP server setup, instructions, and tool registration
- **liggare_tool.py**: `search_liggare` tool — registration, validation, lazy LanceDB connection
- **matrikel_tool.py**: `search_matrikel` tool — registration, validation, lazy LanceDB connection
- **formatter.py**: Formats Liggare and Matrikel search results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3005)
python -m ra_mcp_sjomanshus_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_sjomanshus_mcp.server --port 8080

# stdio transport
python -m ra_mcp_sjomanshus_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-sjomanshus-lib` (which depends on `ra-mcp-common`)
- External: `fastmcp`

## Part of ra-mcp

Composed into the root server alongside the other dataset modules. Tools are registered as bare names (`search_liggare`, `search_matrikel`) and get namespaced as `<module>:<tool>` in the composed server. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

# ra-mcp-filmcensur-mcp

MCP tools for Swedish film censorship records (Filmcensur) search.

## Overview

Thin MCP wrapper around `ra-mcp-filmcensur-lib`. Registers one FastMCP tool — `search_filmreg` — which runs LanceDB full-text search over the Swedish film censorship registry (films reviewed by Statens biografbyrå, 1911-2011) and formats results for LLM consumption. Tools are registered as bare names and get namespaced as `<module>:<tool>` when composed into the root server.

## MCP Tools

### `search_filmreg`

Search Swedish film censorship records. Returns original and Swedish titles, production year/country, category, age rating, number of cuts, producer, free-text descriptions, and notes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across film censorship records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum number of records to return per query |
| `filmkategori` | str \| None | None | Filter: film category (e.g. `Spelfilm`, `Dokumentär`) |
| `produktionsland` | str \| None | None | Filter: production country (e.g. `Sverige`, `USA`) |
| `aaldersgraens` | str \| None | None | Filter: age rating (e.g. `15 år`, `Barntillåten`) |
| `research_context` | str \| None | None | Brief research goal (logging only) |

## Components

- **tools.py**: FastMCP server (`filmcensur_mcp`) setup, instructions, and tool registration
- **filmreg_tool.py**: `search_filmreg` tool registration, lazy LanceDB connection, input validation
- **formatter.py**: `format_filmreg_results` — formats search results for LLM output
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3006)
python -m ra_mcp_filmcensur_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_filmcensur_mcp.server --port 3006

# stdio transport
python -m ra_mcp_filmcensur_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-filmcensur-lib` (backed by `ra-mcp-common` for dataset path resolution)
- External: `fastmcp`

## Part of ra-mcp

Registered into the root composition server, where its bare tool name is namespaced as `<module>:<tool>` (e.g. `filmcensur:search_filmreg`). See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

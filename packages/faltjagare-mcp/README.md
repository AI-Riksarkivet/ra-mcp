# ra-mcp-faltjagare-mcp

MCP tools for Jämtland field regiment soldier records (Fältjägare) search.

## Overview

Thin MCP wrapper around `ra-mcp-faltjagare-lib`. Registers one FastMCP tool — `search_faltjagare` — which runs LanceDB full-text search over the Fältjägare soldier registry and formats results for LLM consumption. Tools are registered as bare names and get namespaced as `<module>:<tool>` when composed into the root server.

## MCP Tools

### `search_faltjagare`

Search Jämtland field regiment soldier records (1645-1901). Returns soldier name, family name, rank, company, parish, region, service period, and fate (killed/died/deserted).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across soldier records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum number of records to return per query |
| `kompani` | str \| None | None | Filter: company name (case-insensitive substring match) |
| `region` | str \| None | None | Filter: region (e.g. `Jämtland`, `Härjedalen`) |
| `befattning` | str \| None | None | Filter: rank/position (e.g. `Soldat`, `Korpral`) |
| `research_context` | str \| None | None | Brief research goal (logging only) |

## Components

- **tools.py**: FastMCP server (`faltjagare_mcp`) setup, instructions, and tool registration
- **faltjagare_tool.py**: `search_faltjagare` tool registration, lazy LanceDB connection, input validation
- **formatter.py**: `format_faltjagare_results` — formats search results for LLM output
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3010)
python -m ra_mcp_faltjagare_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_faltjagare_mcp.server --port 3010

# stdio transport
python -m ra_mcp_faltjagare_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-faltjagare-lib` (backed by `ra-mcp-common` for dataset path resolution)
- External: `fastmcp`

## Part of ra-mcp

Registered into the root composition server, where its bare tool name is namespaced as `<module>:<tool>` (e.g. `faltjagare:search_faltjagare`). See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

# ra-mcp-suffrage-mcp

MCP tools for Swedish women's suffrage records (Rösträtt & FKPR).

## Overview

Thin MCP wrapper around `ra-mcp-suffrage-lib`. Registers two FastMCP tools — `search_rostratt` and `search_fkpr` — each running LanceDB full-text search over a women's suffrage dataset and returning LLM-friendly formatted output. The tools are registered as bare names and get namespaced as `suffrage:<tool>` when composed into the root server.

## MCP Tools

### `search_rostratt`

Search women's suffrage petition signatures 1913-1914 — 29,000 names from 5 counties. Returns signer name, title, occupation, address, town, county, and monetary contributions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across Rösträtt petition records |
| `offset` | int | 0 | Pagination start position (0, 25, 50...) |
| `limit` | int | 25 | Maximum number of records to return per query |
| `lan` | str \| None | None | Optional filter: county name (case-insensitive substring match) |
| `ortens_namn` | str \| None | None | Optional filter: town name (case-insensitive substring match) |
| `research_context` | str \| None | None | Brief summary of the research goal (logging only) |

### `search_fkpr`

Search Gothenburg FKPR suffrage association members 1911-1920 — 1,700 women. Returns name, title/occupation, address, and years of membership.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across FKPR membership records |
| `offset` | int | 0 | Pagination start position (0, 25, 50...) |
| `limit` | int | 25 | Maximum number of records to return per query |
| `research_context` | str \| None | None | Brief summary of the research goal (logging only) |

## Components

- **tools.py**: FastMCP server setup, instructions, and tool registration
- **rostratt_tool.py**: `search_rostratt` tool registration with lazy LanceDB connection
- **fkpr_tool.py**: `search_fkpr` tool registration with lazy LanceDB connection
- **formatter.py**: Formats Rösträtt and FKPR results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3011)
python -m ra_mcp_suffrage_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_suffrage_mcp.server --port 3011

# stdio transport
python -m ra_mcp_suffrage_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-suffrage-lib` (depends on `ra-mcp-common`)
- External: `fastmcp`

## Part of ra-mcp

Composed into the root server alongside the other dataset modules. Tools are registered as bare names (`search_rostratt`, `search_fkpr`) and get namespaced as `suffrage:<tool>` in the composed server. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

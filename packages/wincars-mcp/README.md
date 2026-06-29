# ra-mcp-wincars-mcp

MCP tools for Norrland vehicle registration records (Wincars) search.

## Overview

Thin MCP wrapper around `ra-mcp-wincars-lib`. Registers a single FastMCP tool — `search_wincars` — that runs LanceDB full-text search over the Norrland vehicle register and returns LLM-friendly formatted output. The tool is registered as a bare name and gets namespaced as `wincars:<tool>` when composed into the root server.

## MCP Tools

### `search_wincars`

Search the Norrland vehicle register 1916-1972 — 1.5 million vehicles across 5 northern Swedish counties (Gävleborg, Jämtland, Norrbotten, Västerbotten, Västernorrland). Returns registration number, vehicle type, make/model, year, chassis/engine numbers, registration/deregistration dates, domicile, and status (active/written off/scrapped).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across vehicle registration records |
| `offset` | int | 0 | Pagination start position (0, 25, 50...) |
| `limit` | int | 25 | Maximum number of records to return per query |
| `typ` | str \| None | None | Optional filter: vehicle type code (e.g. 'PB'=car, 'MC'=motorcycle, 'LB'=truck, 'SL'=trailer, 'TR'=tractor, 'BS'=bus) |
| `hemvist` | str \| None | None | Optional filter: domicile/location (case-insensitive substring match) |
| `fabrikat` | str \| None | None | Optional filter: make/manufacturer (case-insensitive substring match) |
| `research_context` | str \| None | None | Brief summary of the research goal (logging only) |

## Components

- **tools.py**: FastMCP server setup, instructions, and tool registration
- **wincars_tool.py**: `search_wincars` tool registration with lazy LanceDB connection
- **formatter.py**: Formats Wincars results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3014)
python -m ra_mcp_wincars_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_wincars_mcp.server --port 3014

# stdio transport
python -m ra_mcp_wincars_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-wincars-lib` (depends on `ra-mcp-common`)
- External: `fastmcp`

## Part of ra-mcp

Composed into the root server alongside the other dataset modules. The tool is registered as a bare name (`search_wincars`) and gets namespaced as `wincars:<tool>` in the composed server. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

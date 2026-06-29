# ra-mcp-rosenberg-mcp

MCP tools for Rosenberg's geographical lexicon of Sweden.

## Overview

Thin MCP wrapper around `ra-mcp-rosenberg-lib`. Registers one FastMCP tool — `search_rosenberg` — which runs LanceDB full-text search over Rosenberg's *Geografiskt-statistiskt handlexikon öfver Sverige* (historical Swedish places and their descriptions) and formats results for LLM consumption. Tools are registered as bare names and get namespaced as `<module>:<tool>` when composed into the root server.

## MCP Tools

### `search_rosenberg`

Search Rosenberg's geographical lexicon of Sweden. Returns place name, parish, hundred, county, full description text, and industry/feature flags.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across the lexicon |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum number of records to return per query |
| `lan` | str \| None | None | Filter: county/län (e.g. `Stockholms`, `Malmöhus`) |
| `forsamling` | str \| None | None | Filter: parish/församling (e.g. `Klara`, `Hedvig`) |
| `research_context` | str \| None | None | Brief research goal (logging only) |

## Components

- **tools.py**: FastMCP server (`rosenberg_mcp`) setup, instructions, and tool registration
- **rosenberg_tool.py**: `search_rosenberg` tool registration, lazy LanceDB connection, input validation
- **formatter.py**: `format_rosenberg_results` — formats search results for LLM output
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3007)
python -m ra_mcp_rosenberg_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_rosenberg_mcp.server --port 3007

# stdio transport
python -m ra_mcp_rosenberg_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-rosenberg-lib` (backed by `ra-mcp-common` for dataset path resolution)
- External: `fastmcp`

## Part of ra-mcp

Registered into the root composition server, where its bare tool name is namespaced as `<module>:<tool>` (e.g. `rosenberg:search_rosenberg`). See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

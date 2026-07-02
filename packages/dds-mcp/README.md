# ra-mcp-dds-mcp

MCP tools for Swedish church records (DDS) search — births, deaths, marriages.

## Overview

Thin MCP wrapper around `ra-mcp-dds-lib`. Registers three FastMCP tools — `search_fodelse`, `search_doda`, and `search_vigsel` — backed by a lazily-opened LanceDB connection. The dataset covers Swedish church records (Demografisk Databas Södra Sverige) for births/baptisms, deaths, and marriages from the 1600s to the early 1900s across multiple Swedish counties. Each tool runs full-text search over its LanceDB table and returns LLM-formatted plain text.

Tools are registered as bare names (`search_fodelse`, `search_doda`, `search_vigsel`) and get namespaced as `dds:<tool>` when composed into the root server.

## MCP Tools

### `search_fodelse`

Search Swedish birth/baptism records — 1.3 million records from 1600s-1914. Returns child name, gender, parents (father/mother names, occupations), birth/baptism date, parish, county, and birth place.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across birth/baptism records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `forsamling` | str \| None | None | Optional filter: parish name (case-insensitive substring match) |
| `lan` | str \| None | None | Optional filter: county name (case-insensitive substring match) |
| `kon` | str \| None | None | Optional filter: gender (e.g. 'Man', 'Kvinna'; substring match) |
| `datum_from` | str \| None | None | Optional filter: earliest date (YYYY-MM-DD, inclusive) |
| `datum_till` | str \| None | None | Optional filter: latest date (YYYY-MM-DD, inclusive) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

### `search_doda`

Search Swedish death records — 950,000 records from 1600s-1951. Returns name, occupation, home parish, age, cause of death, relative information, and archive reference.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across death records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `forsamling` | str \| None | None | Optional filter: parish name (case-insensitive substring match) |
| `lan` | str \| None | None | Optional filter: county name (case-insensitive substring match) |
| `dodsorsak` | str \| None | None | Optional filter: cause of death (case-insensitive substring match) |
| `datum_from` | str \| None | None | Optional filter: earliest date (YYYY-MM-DD, inclusive) |
| `datum_till` | str \| None | None | Optional filter: latest date (YYYY-MM-DD, inclusive) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

### `search_vigsel`

Search Swedish marriage records — 447,000 records from 1600s-1929. Returns bride and groom names, occupations, ages, civil status, home parishes, and banns dates.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across marriage records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `forsamling` | str \| None | None | Optional filter: parish name (case-insensitive substring match) |
| `lan` | str \| None | None | Optional filter: county name (case-insensitive substring match) |
| `datum_from` | str \| None | None | Optional filter: earliest date (YYYY-MM-DD, inclusive) |
| `datum_till` | str \| None | None | Optional filter: latest date (YYYY-MM-DD, inclusive) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

## Components

- **tools.py**: FastMCP server (`dds_mcp`) setup, instructions, and tool registration
- **fodelse_tool.py**: `search_fodelse` tool registration and LanceDB connection handling
- **doda_tool.py**: `search_doda` tool registration and LanceDB connection handling
- **vigsel_tool.py**: `search_vigsel` tool registration and LanceDB connection handling
- **formatter.py**: Formats birth, death, and marriage results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, streamable-http on /mcp)
python -m ra_mcp_dds_mcp.server --port 3013

# stdio transport
python -m ra_mcp_dds_mcp.server --stdio
```

The default port is `3013` (overridable via the `PORT` environment variable or `--port`).

## Dependencies

- Internal: `ra-mcp-dds-lib`
- External: `fastmcp==3.4.2`

## Part of ra-mcp

Tools are registered as bare names and get namespaced as `dds:<tool>` when composed into the root server via the `AVAILABLE_MODULES` registry. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

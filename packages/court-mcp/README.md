# ra-mcp-court-mcp

MCP tools for Swedish court records (Domboksregister & Medelstad) search.

## Overview

Thin MCP wrapper around `ra-mcp-court-lib`. Registers two FastMCP tools — `search_domboksregister` and `search_medelstad` — backed by a lazily-opened LanceDB connection. The dataset covers two härad court collections: Västra härad (Domboksregister) and Medelstad härad. Both tools run full-text search over the LanceDB tables and return LLM-formatted plain text.

Tools are registered as bare names (`search_domboksregister`, `search_medelstad`) and get namespaced as `court:<tool>` when composed into the root server.

## MCP Tools

### `search_domboksregister`

Search Västra härad court records 1611-1730 — 88,000 persons in court cases. Returns person name, role (plaintiff/defendant), title, parish, place, case notes, date, and case type.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across Domboksregister records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `roll` | str \| None | None | Optional filter: role in case (e.g. 'Kärande', 'Svarande'; substring match) |
| `socken` | str \| None | None | Optional filter: parish name (case-insensitive substring match) |
| `datum_from` | str \| None | None | Optional filter: date range start inclusive (string comparison on `datum`) |
| `datum_till` | str \| None | None | Optional filter: date range end inclusive (string comparison on `datum`) |
| `arende` | str \| None | None | Optional filter: case type (substring match on `arende`) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

### `search_medelstad`

Search Medelstad härad court books 1668-1750 — 91,000 persons with 21,000 case summaries. Returns person name, title, parish, court date, case type, and full case summary text.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across Medelstad records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `mal_typ` | str \| None | None | Optional filter: case type (case-insensitive substring match) |
| `norm_forsamling` | str \| None | None | Optional filter: parish name (case-insensitive substring match) |
| `datum_from` | str \| None | None | Optional filter: date range start inclusive (string comparison on `ting_dag`) |
| `datum_till` | str \| None | None | Optional filter: date range end inclusive (string comparison on `ting_dag`) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

## Components

- **tools.py**: FastMCP server (`court_mcp`) setup, instructions, and tool registration
- **domboksregister_tool.py**: `search_domboksregister` tool registration and LanceDB connection handling
- **medelstad_tool.py**: `search_medelstad` tool registration and LanceDB connection handling
- **formatter.py**: Formats Domboksregister and Medelstad results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, streamable-http on /mcp)
python -m ra_mcp_court_mcp.server --port 3008

# stdio transport
python -m ra_mcp_court_mcp.server --stdio
```

The default port is `3008` (overridable via the `PORT` environment variable or `--port`).

## Dependencies

- Internal: `ra-mcp-court-lib`
- External: `fastmcp==3.1.1`

## Part of ra-mcp

Tools are registered as bare names and get namespaced as `court:<tool>` when composed into the root server via the `AVAILABLE_MODULES` registry. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

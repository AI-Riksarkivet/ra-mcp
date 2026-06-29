# ra-mcp-specialsok-mcp

MCP tools for Specialsök datasets (flygvapen, fångrullor, kurhuset, press, video).

## Overview

Thin MCP wrapper around `ra-mcp-specialsok-lib`. Registers five FastMCP tools — `search_flygvapen`, `search_fangrullor`, `search_kurhuset`, `search_press`, and `search_video` — each running full-text search over its own table in a local LanceDB copy of the Riksarkivet Specialsök datasets. Tools are registered as bare names and get namespaced as `<module>:<tool>` when composed into the root server.

## MCP Tools

### `search_flygvapen`

Search Swedish military aviation accidents (Flygvapenhaverier) with aircraft types, crash sites, and summaries.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across aviation accident records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `fpl_typ` | str \| None | None | Filter: aircraft type (case-insensitive substring, e.g. `J 35`) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

### `search_fangrullor`

Search Östersund prison records (Fångrullor) — inmates with names, ages, crimes, and home parishes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across prison records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `brott` | str \| None | None | Filter: crime type (case-insensitive substring, e.g. `stöld` for theft) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

### `search_kurhuset`

Search hospital patient records (Kurhuset) with diagnoses, treatments, and outcomes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across hospital patient records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `sjukdom` | str \| None | None | Filter: disease name (case-insensitive substring, e.g. `syfilis`) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

### `search_press`

Search Swedish government press conferences (Presskonferenser) with titles and content descriptions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across press conference records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `aar` | str \| None | None | Filter: year (case-insensitive substring, e.g. `2005`) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

### `search_video`

Search Swedish video rental stores (Videobutiker) across Sweden.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across video store records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records per query |
| `laen` | str \| None | None | Filter: county name (case-insensitive substring, e.g. `Stockholm`) |
| `kommun` | str \| None | None | Filter: municipality name (case-insensitive substring) |
| `research_context` | str \| None | None | Research goal summary (logging only) |

## Components

- **tools.py**: FastMCP server setup, instructions, and registration of all five tools
- **flygvapen_tool.py**: `search_flygvapen` tool (Flygvapenhaverier table)
- **fangrullor_tool.py**: `search_fangrullor` tool (Fångrullor table)
- **kurhuset_tool.py**: `search_kurhuset` tool (Kurhuset table)
- **press_tool.py**: `search_press` tool (Presskonferenser table)
- **video_tool.py**: `search_video` tool (Videobutiker table)
- **formatter.py**: Formats each dataset's search results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3012)
python -m ra_mcp_specialsok_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_specialsok_mcp.server --port 8080

# stdio transport
python -m ra_mcp_specialsok_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-specialsok-lib` (which depends on `ra-mcp-common`)
- External: `fastmcp`

## Part of ra-mcp

Composed into the root server alongside the other dataset modules. Tools are registered as bare names (`search_flygvapen`, `search_fangrullor`, `search_kurhuset`, `search_press`, `search_video`) and get namespaced as `<module>:<tool>` in the composed server. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

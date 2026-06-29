# ra-mcp-search-mcp

MCP tools for searching Riksarkivet transcribed documents.

## Overview

Thin MCP wrapper around `ra-mcp-search-lib`. Registers two FastMCP tools with full parameter validation, session-based deduplication, pagination info, and LLM-friendly formatted output.

The tools are registered under bare names — `transcribed` and `metadata` (see `@mcp.tool(name=...)` in `search_tool.py`). When the root server composes this provider it adds the `search` namespace, so clients of the composed server call them as `search_transcribed` and `search_metadata`. In standalone mode (running this server directly) the names are the bare `transcribed` and `metadata`.

## MCP Tools

### `transcribed` (namespaced: `search_transcribed`)

Search AI-transcribed text across ~1.6M digitised pages. Supports Solr query syntax: wildcards (`troll*`), fuzzy (`stockholm~1`), Boolean (`(A AND B)`), proximity (`"term1 term2"~10`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term or Solr query |
| `offset` | int | *(required)* | Pagination start (0, 50, 100...) |
| `limit` | int | 25 | Documents per page |
| `max_snippets_per_record` | int | 3 | Max matching pages per document |
| `max_response_tokens` | int | 15000 | Response token budget |
| `sort` | str | `relevance` | `relevance`, `timeAsc`, `timeDesc`, `alphaAsc`, `alphaDesc` |
| `year_min` | int \| None | None | Start year filter |
| `year_max` | int \| None | None | End year filter |
| `dedup` | bool | True | Session deduplication |
| `research_context` | str \| None | None | Research goal (telemetry) |

### `metadata` (namespaced: `search_metadata`)

Search document metadata (titles, names, places, descriptions) across 2M+ catalog records. Unlike `transcribed`, this tool has no `max_snippets_per_record` parameter (metadata search returns no page snippets).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Free-text search |
| `offset` | int | *(required)* | Pagination start |
| `only_digitised` | bool | True | Limit to digitised materials |
| `limit` | int | 25 | Documents per page |
| `max_response_tokens` | int | 15000 | Response token budget |
| `sort` | str | `relevance` | `relevance`, `timeAsc`, `timeDesc`, `alphaAsc`, `alphaDesc` |
| `year_min` | int \| None | None | Start year filter |
| `year_max` | int \| None | None | End year filter |
| `name` | str \| None | None | Person name filter |
| `place` | str \| None | None | Place name filter |
| `dedup` | bool | True | Session deduplication |
| `research_context` | str \| None | None | Research goal (telemetry) |

## Components

- **tools.py**: FastMCP server setup and LLM instructions
- **search_tool.py**: Tool registration, input validation, pagination, and dedup logic
- **formatter.py**: `PlainTextFormatter` — formats search results for LLM consumption

## Standalone Usage

The default transport is HTTP (streamable-http) on port 3001. Pass `--stdio` for stdio transport.

```bash
# HTTP transport (default) — serves http://localhost:3001/mcp
python -m ra_mcp_search_mcp.server
python -m ra_mcp_search_mcp.server --port 3001

# stdio transport
python -m ra_mcp_search_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-search-lib`
- External: `fastmcp`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with namespace `search`. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

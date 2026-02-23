# ra-mcp-search-mcp

MCP tools for searching Riksarkivet transcribed documents.

## Overview

Thin MCP wrapper around `ra-mcp-search`. Registers two FastMCP tools — `search_transcribed` and `search_metadata` — with full parameter validation, session-based deduplication, pagination info, and LLM-friendly formatted output.

## MCP Tools

### `search_transcribed`

Search AI-transcribed text across ~1.6M digitised pages. Supports Solr query syntax: wildcards (`troll*`), fuzzy (`stockholm~1`), Boolean (`(A AND B)`), proximity (`"term1 term2"~10`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term or Solr query |
| `offset` | int | *(required)* | Pagination start (0, 50, 100...) |
| `limit` | int | 25 | Documents per page |
| `sort` | str | `relevance` | `relevance`, `timeAsc`, `timeDesc`, `alphaAsc`, `alphaDesc` |
| `year_min` | int \| None | None | Start year filter |
| `year_max` | int \| None | None | End year filter |
| `max_snippets_per_record` | int | 3 | Max matching pages per document |
| `max_response_tokens` | int | 15000 | Response token budget |
| `dedup` | bool | True | Session deduplication |
| `research_context` | str \| None | None | Research goal (telemetry) |

### `search_metadata`

Search document metadata (titles, names, places, descriptions) across 2M+ catalog records.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Free-text search |
| `offset` | int | *(required)* | Pagination start |
| `name` | str \| None | None | Person name filter |
| `place` | str \| None | None | Place name filter |
| `only_digitised` | bool | True | Limit to digitised materials |
| *(plus same shared params as search_transcribed)* | | | |

## Components

- **tools.py**: FastMCP server setup and LLM instructions
- **search_tool.py**: Tool registration, input validation, pagination, and dedup logic
- **formatter.py**: `PlainTextFormatter` — formats search results for LLM consumption

## Standalone Usage

```bash
# stdio transport
python -m ra_mcp_search_mcp.server

# HTTP transport
python -m ra_mcp_search_mcp.server --port 3001
```

## Dependencies

- Internal: `ra-mcp-search`
- External: `fastmcp`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with namespace `search`. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

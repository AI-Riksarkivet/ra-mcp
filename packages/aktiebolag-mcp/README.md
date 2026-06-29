# ra-mcp-aktiebolag-mcp

MCP tools for Swedish joint-stock company records (Aktiebolag 1901-1935) search.

## Overview

Thin MCP wrapper around `ra-mcp-aktiebolag-lib`. Registers two FastMCP tools — `search_bolag` and `search_styrelse` — backed by a lazily-opened LanceDB connection. The dataset covers Swedish joint-stock companies 1901-1935 (companies with >100,000 kr capital) and their board members. Both tools run full-text search over the LanceDB tables and return LLM-formatted plain text.

Tools are registered as bare names (`search_bolag`, `search_styrelse`) and get namespaced as `aktiebolag:<tool>` when composed into the root server.

## MCP Tools

### `search_bolag`

Search Swedish joint-stock companies 1901-1935 — 12,500 companies with >100,000 kr capital. Returns company name, purpose, address, board seat city, managing director, share capital, and board member names.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across company records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `styrelsesate` | str \| None | None | Optional filter: board seat city (case-insensitive substring match) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

### `search_styrelse`

Search board members of Swedish companies 1901-1935 — 49,000 board members. Returns member name, title, gender, and company name.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across board member records |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum records to return per query |
| `titel` | str \| None | None | Optional filter: title (case-insensitive substring match) |
| `research_context` | str \| None | None | Brief summary of research goal (logging only) |

## Components

- **tools.py**: FastMCP server (`aktiebolag_mcp`) setup, instructions, and tool registration
- **bolag_tool.py**: `search_bolag` tool registration and LanceDB connection handling
- **styrelse_tool.py**: `search_styrelse` tool registration and LanceDB connection handling
- **formatter.py**: Formats company and board-member results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, streamable-http on /mcp)
python -m ra_mcp_aktiebolag_mcp.server --port 3009

# stdio transport
python -m ra_mcp_aktiebolag_mcp.server --stdio
```

The default port is `3009` (overridable via the `PORT` environment variable or `--port`).

## Dependencies

- Internal: `ra-mcp-aktiebolag-lib`
- External: `fastmcp==3.1.1`

## Part of ra-mcp

Tools are registered as bare names and get namespaced as `aktiebolag:<tool>` when composed into the root server via the `AVAILABLE_MODULES` registry. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

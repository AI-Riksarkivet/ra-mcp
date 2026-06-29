# ra-mcp-sbl-mcp

MCP tools for Svenskt biografiskt lexikon (SBL) search.

## Overview

Thin MCP wrapper around `ra-mcp-sbl-lib`. Registers four FastMCP tools — `search_sbl`, `view_sbl_article`, `load_sbl_article`, and `get_sbl_state` — plus a UI resource for a rich article viewer (MCP App). `search_sbl` runs LanceDB full-text search over SBL biographical articles; the view/load/state tools drive an interactive article viewer. Tools are registered as bare names and get namespaced as `<module>:<tool>` when composed into the root server.

## MCP Tools

### `search_sbl`

Search Svenskt biografiskt lexikon biographical articles. Returns name, occupation, career details (CV/meriter), birth/death dates and places, sources, and portrait image URLs. SBL text uses printed-encyclopedia abbreviations (e.g. `f`=född, `d`=död, `Sthlm`=Stockholm) that should be expanded when presenting.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term for full-text search across SBL articles |
| `offset` | int | 0 | Pagination start position (0, 25, 50, ...) |
| `limit` | int | 25 | Maximum number of records to return per query |
| `gender` | str \| None | None | Filter: `m` (male), `f` (female), or `-` (family/other), exact match |
| `occupation` | str \| None | None | Filter: occupation (case-insensitive substring match) |
| `birth_place` | str \| None | None | Filter: birth place (case-insensitive substring match) |
| `death_place` | str \| None | None | Filter: death place (case-insensitive substring match) |
| `birth_year_min` | int \| None | None | Filter: minimum birth year (inclusive) |
| `birth_year_max` | int \| None | None | Filter: maximum birth year (inclusive) |
| `death_year_min` | int \| None | None | Filter: minimum death year (inclusive) |
| `death_year_max` | int \| None | None | Filter: maximum death year (inclusive) |
| `research_context` | str \| None | None | Brief research goal (logging only) |

### `view_sbl_article`

Display an SBL article in a rich viewer (creates a new viewer; model- and app-visible). Takes an `article_id` from `search_sbl` results and shows the full article with portrait, career details, printed works, sources, and a link to the full biography on the SBL website.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `article_id` | int | *(required)* | The SBL article ID from `search_sbl` results |

### `load_sbl_article`

Load an SBL article into the viewer in place (app-only, for cross-reference navigation).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `article_id` | int | *(required)* | The SBL article ID to load |
| `view_id` | str | `""` | The view ID from the initial tool result |

### `get_sbl_state`

Return the current article for a specific view (app-only, polling endpoint for LLM-initiated loads).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `view_id` | str | `""` | The view ID to get state for |

## Components

- **tools.py**: FastMCP server (`sbl_mcp`) setup, instructions, and registration of both the search and viewer tools
- **sbl_tool.py**: `search_sbl` tool registration, lazy LanceDB connection, input validation
- **view_tool.py**: `view_sbl_article`, `load_sbl_article`, `get_sbl_state` tools and the `ui://sbl-article-viewer/mcp-app.html` UI resource
- **state.py**: Per-view in-memory state store for the article viewer
- **formatter.py**: `format_sbl_results` — formats search results for LLM output
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3004)
python -m ra_mcp_sbl_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_sbl_mcp.server --port 3004

# stdio transport
python -m ra_mcp_sbl_mcp.server --stdio
```

The viewer UI is served from a built bundle in `src/ra_mcp_sbl_mcp/dist/`; run `npm run build` in `packages/sbl-mcp/` if the resource is missing.

## Dependencies

- Internal: `ra-mcp-sbl-lib` (backed by `ra-mcp-common` for dataset path resolution)
- External: `fastmcp`

## Part of ra-mcp

Registered into the root composition server, where each bare tool name is namespaced as `<module>:<tool>` (e.g. `sbl:search_sbl`, `sbl:view_sbl_article`). See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

# Search

Domain package for searching transcribed documents via the Riksarkivet Search
API (`ra-mcp-search-lib`, module `ra_mcp_search_lib`).

## Models

Source: [`packages/libs/search-lib/src/ra_mcp_search_lib/models.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/libs/search-lib/src/ra_mcp_search_lib/models.py)

Pydantic models for the Search API surface — `SearchRecord`, `RecordsResponse`
(the raw `/api/records` payload), and `SearchResult` (the enriched result the
operations layer returns).

## Client

Source: [`packages/libs/search-lib/src/ra_mcp_search_lib/search_client.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/libs/search-lib/src/ra_mcp_search_lib/search_client.py)

`SearchClient` is a thin, typed wrapper over the `/api/records` endpoint with
direct Pydantic parsing. It takes an injected `HTTPClient` and is traced under
`ra_mcp.search.client`.

## Operations

Source: [`packages/libs/search-lib/src/ra_mcp_search_lib/search_operations.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/libs/search-lib/src/ra_mcp_search_lib/search_operations.py)

`SearchOperations` holds the business logic shared by the CLI, TUI, and MCP
tools — keyword search across transcribed text and metadata, pagination, and
snippet assembly. Traced under `ra_mcp.search_operations` and metered with
`ra_mcp.search.requests` / `ra_mcp.search.results`.

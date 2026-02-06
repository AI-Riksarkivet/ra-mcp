# ra-mcp-search

Search domain package for Riksarkivet transcribed documents.

## Components

- **models.py**: Pydantic models (`SearchRecord`, `RecordsResponse`, `SearchResult`)
- **clients/search_client.py**: `SearchAPI` client for the Riksarkivet records API
- **operations/search_operations.py**: Search business logic
- **config.py**: API URL and default constants

## Dependencies

- `ra-mcp-common`: Shared HTTP client

## Part of ra-mcp

Used by `ra-mcp-search-mcp` (MCP tools) and `ra-mcp-search-cli` (CLI command).

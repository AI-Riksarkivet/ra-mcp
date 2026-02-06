# ra-mcp-common

Shared HTTP client and utilities for all ra-mcp packages.

## Components

- **utils/http_client.py**: Centralized urllib-based HTTP client with configurable logging and timeouts

## Environment Variables

- `RA_MCP_LOG_API`: Enable API call logging to `ra_mcp_api.log`
- `RA_MCP_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `RA_MCP_TIMEOUT`: Override default request timeout in seconds

## Part of ra-mcp

This package has no internal dependencies and is used by all other ra-mcp packages.

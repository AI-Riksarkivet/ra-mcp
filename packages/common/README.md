# ra-mcp-common

Shared HTTP client and utilities for all ra-mcp packages.

## Overview

This is the foundation package with **no internal dependencies**. It provides the centralized HTTP client used by every other ra-mcp package, along with telemetry helpers and common formatting utilities.

## Components

- **utils/http_client.py**: `HTTPClient` — urllib-based HTTP client with automatic retry (exponential backoff on 429/5xx), OpenTelemetry instrumentation, and configurable logging
- **utils/formatting.py**: Shared formatting helpers (page ID parsing, error message formatting)
- **telemetry.py**: `get_tracer()` and `get_meter()` — thin wrappers around the OpenTelemetry API that work as no-ops when the SDK is not initialized

## Usage

```python
from ra_mcp_common.utils.http_client import HTTPClient

client = HTTPClient()

# JSON API calls
data = client.get_json("https://data.riksarkivet.se/api/records", params={"q": "Stockholm"})

# XML responses (returns bytes)
xml = client.get_xml("https://sok.riksarkivet.se/dokument/alto/...", timeout=30)

# Raw content (returns None on 404/errors instead of raising)
content = client.get_content("https://example.com/resource")
```

The default singleton `default_http_client` is used by all domain packages. For CLI commands with `--log`, use `get_http_client(enable_logging=True)`.

## HTTP Client Behavior

- **Retry**: Automatic retry with exponential backoff on status codes 429, 500, 502, 503, 504 and on `TimeoutError`/`URLError`. Default: 3 retries, 0.5s base backoff.
- **User-Agent**: `ra-mcp/{version}` (auto-detected from package metadata)
- **Telemetry**: Every request produces an `HTTP GET` span plus counters for requests, errors, duration, and response size.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RA_MCP_LOG_API` | *(unset)* | Enable API call logging to `ra_mcp_api.log` |
| `RA_MCP_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `RA_MCP_TIMEOUT` | `60` | Override default request timeout in seconds |

## Dependencies

- External: `opentelemetry-api`

## Part of ra-mcp

This package has no internal dependencies and is used by all other ra-mcp packages. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

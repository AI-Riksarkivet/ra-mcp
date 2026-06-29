# ra-mcp-common

Shared HTTP client and utilities for all ra-mcp packages.

## Overview

This is the foundation package with **no internal dependencies**. It provides the centralized HTTP client used by every other ra-mcp package, along with telemetry helpers and common formatting utilities.

## Components

- **http_client.py**: `HTTPClient` — async HTTP client built on `httpx.AsyncClient`, with automatic retry (exponential backoff on 429/5xx), connection pooling, optional HTTP/2, OpenTelemetry instrumentation, and configurable logging
- **formatting.py**: Shared formatting helpers (page ID parsing, error message formatting)
- **datasets.py**: `resolve_dataset_path(name)` — resolves a LanceDB dataset path with a four-step fallback: `<NAME>_LANCEDB_URI` env var → local `data/<name>/` (development) → `<RA_MCP_DATA_DIR>/<name>/` mount point (Docker) → `hf://datasets/carpelan/<name>-lance` (HuggingFace remote)
- **telemetry.py**: `get_tracer()` and `get_meter()` — thin wrappers around the OpenTelemetry API that work as no-ops when the SDK is not initialized

## Usage

The HTTP client is async — its methods are coroutines and must be awaited.

```python
import asyncio

from ra_mcp_common.http_client import HTTPClient


async def main():
    client = HTTPClient()  # optional: HTTPClient(http2=True) when the [http2] extra is installed
    try:
        # JSON API calls
        data = await client.get_json("https://data.riksarkivet.se/api/records", params={"q": "Stockholm"})

        # XML responses (returns bytes)
        xml = await client.get_xml("https://sok.riksarkivet.se/dokument/alto/...", timeout=30)

        # Raw content (returns None on 404/errors instead of raising)
        content = await client.get_content("https://example.com/resource")
    finally:
        await client.aclose()  # close the underlying httpx client


asyncio.run(main())
```

The default singleton `default_http_client` is used by all domain packages. For CLI commands with `--log`, use `get_http_client(enable_logging=True)`.

## HTTP Client Behavior

- **Retry**: Automatic retry with exponential backoff on status codes 429, 500, 502, 503, 504 and on `httpx.TimeoutException`/`httpx.ConnectError`. Default: 3 retries, 0.5s base backoff.
- **Connection pooling**: Reuses connections via `httpx.AsyncClient` (max 20 connections, 10 keep-alive), follows redirects, and uses granular connect/read/write/pool timeouts.
- **User-Agent**: `ra-mcp/{version}` (auto-detected from package metadata)
- **Telemetry**: Every request produces an `HTTP GET` span plus counters for requests, errors, retries, duration, and response size.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RA_MCP_LOG_API` | *(unset)* | Enable API call logging to `ra_mcp_api.log` |
| `RA_MCP_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `RA_MCP_TIMEOUT` | `60` | Override default request timeout in seconds |
| `RA_MCP_DATA_DIR` | `/data` | Mount point searched by `datasets.py` for LanceDB datasets |
| `<NAME>_LANCEDB_URI` | *(unset)* | Per-dataset override for `resolve_dataset_path` (e.g. `DDS_LANCEDB_URI`) |

## Dependencies

- External: `httpx>=0.28.0`, `opentelemetry-api>=1.28.0`
- Optional extra: `[http2]` adds `httpx[http2]>=0.28.0` for HTTP/2 support

## Part of ra-mcp

This package has no internal dependencies and is used by all other ra-mcp packages. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

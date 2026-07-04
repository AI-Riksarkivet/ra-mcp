# Common

Shared utilities used across every ra-mcp package (`ra-mcp-common`, module
`ra_mcp_common`). No internal dependencies.

## HTTP Client

Source: [`packages/libs/common/src/ra_mcp_common/http_client.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/libs/common/src/ra_mcp_common/http_client.py)

`HTTPClient` is the centralized async `httpx` client used by every domain
library. It adds exponential-backoff retry on transient failures (429, 500,
502, 503, 504, timeouts, connection errors), structured logging, and
OpenTelemetry spans/metrics.

| Member | Description |
|--------|-------------|
| `HTTPClient(...)` | Construct a client with per-timeout, retry, and connection-pool settings. |
| `get_json(url, params=None, timeout=30, headers=None)` | GET and parse a JSON response. |
| `get_xml(url, params=None, timeout=30, headers=None)` | GET raw XML bytes. |
| `get_content(url, timeout=30, headers=None)` | GET raw bytes; returns `None` on 404/non-200. |
| `aclose()` | Close the underlying `httpx.AsyncClient`. |
| `default_http_client` / `get_http_client(enable_logging=False)` | Shared singleton accessor. |

## Formatting Utilities

Source: [`packages/libs/common/src/ra_mcp_common/formatting.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/libs/common/src/ra_mcp_common/formatting.py)

Presentation helpers shared by the CLI and MCP formatters (text truncation,
snippet highlighting, reference-code formatting).

## Datasets

Source: [`packages/libs/common/src/ra_mcp_common/datasets.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/libs/common/src/ra_mcp_common/datasets.py)

Resolves LanceDB dataset paths for the optional dataset modules, with a
local → mount → Hugging Face Hub fallback chain.

## Telemetry

Source: [`packages/libs/common/src/ra_mcp_common/telemetry.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/libs/common/src/ra_mcp_common/telemetry.py)

Thin wrappers over `opentelemetry-api` that return no-op instances when no SDK
is configured (zero overhead when telemetry is disabled).

| Member | Description |
|--------|-------------|
| `get_tracer(name)` | Get a tracer for a component (e.g. `ra_mcp.http_client`). |
| `get_meter(name)` | Get a meter for a component. |
| `record_span_exception(logger, exc)` | Record an exception as a structured `exception.*` log record (the OTel-recommended replacement for the deprecated span-event API). |

See [Observability](../development/observability.md) for the full instrumentation map.

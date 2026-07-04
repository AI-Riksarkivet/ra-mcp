# Observability

Telemetry is gated on `RA_MCP_OTEL_ENABLED=true`. When enabled, traces, metrics, and logs are exported via OTLP.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RA_MCP_OTEL_ENABLED` | `false` | Master switch |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Collector endpoint |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc` | `grpc` or `http/protobuf` |
| `OTEL_SERVICE_NAME` | `ra-mcp` | Service name (`service.name`) |
| `ENVIRONMENT` | _(unset)_ | `deployment.environment.name` resource attribute (falls back to `DEPLOYMENT_ENVIRONMENT`) |
| `RA_MCP_OTEL_LOG_BRIDGE` | `true` | Bridge Python logging to OTel |

The SDK sets `service.name`, `service.version`, and — when `ENVIRONMENT` is
set — `deployment.environment.name` as resource attributes;
`OTEL_RESOURCE_ATTRIBUTES` is merged on top.

## Trace Tree

Every MCP tool call produces a trace spanning from the protocol layer down to HTTP:

``` mermaid
graph TD
  A["tools/call search_transcribed\n<i>FastMCP — automatic</i>"]
  B["delegate search_transcribed\n<i>FastMCP — composed server</i>"]
  C["tools/call search_transcribed\n<i>FastMCP — provider</i>"]
  D["SearchOperations.search\n<i>domain layer</i>"]
  E["SearchClient.search\n<i>API client</i>"]
  F["HTTP GET\n<i>HTTP client</i>"]

  A --> B --> C --> D --> E --> F
```

## Instrumented Components

| Component | Tracer name | Spans | Metrics |
|-----------|-------------|-------|---------|
| HTTP client | `ra_mcp.http_client` | `HTTP GET` | request count, error count, retry count, duration, response size |
| Search client | `ra_mcp.search.client` | `SearchClient.search` | — |
| Search ops | `ra_mcp.search_operations` | `SearchOperations.search` | `ra_mcp.search.requests`, `ra_mcp.search.results` |
| Browse ops | `ra_mcp.browse_operations` | `BrowseOperations.browse_document`, `BrowseOperations._fetch_page_contexts` | `ra_mcp.browse.requests`, `ra_mcp.browse.pages`, `ra_mcp.browse.empty_pages` |
| ALTO client | `ra_mcp.alto_client` | `ALTOClient.fetch_content` | `ra_mcp.alto.fetches` |
| IIIF client | `ra_mcp.iiif_client` | `IIIFClient.get_collection`, `IIIFClient.fetch_manifest` | — |
| OAI-PMH client | `ra_mcp.oai_pmh_client` | `OAIPMHClient.get_metadata`, `OAIPMHClient.extract_manifest_id` | `ra_mcp.oai_pmh.fetches` |
| Viewer fetchers | fastmcp tracer (`fetchers.py`) | `fetch_text_layer` | — |
| CLI commands | `ra_mcp.cli.*` | `cli.search`, `cli.browse` | — |

FastMCP adds automatic spans for all `tools/call` and `resources/read` operations.

Custom metrics all declare a UCUM unit (`s`, `By`, or an annotation such as
`{request}` / `{fetch}` / `{page}`); metric dimensions are kept low-cardinality
(method, status, result enums), while per-request identifiers (URLs, PIDs,
reference codes, keywords, session ids) live on spans only.

## Error recording

Failures set `span.set_status(ERROR, "{ErrorClass}: …")` and emit a structured
`exception.*` log record via `record_span_exception()` — the OTel Span Event API
(`record_exception`) is deprecated, and the log record carries the active
`trace_id`/`span_id` through the log bridge. Retried-then-succeeded requests
stay `UNSET`.

## Coverage gap

The 13 LanceDB dataset libraries (`*-lib`: diplomatics, sbl, sjomanshus, …) and
`tora-lib` currently have **no manual spans** around their LanceDB full-text
queries, and `pdf-mcp` has no instrumentation. Instrumenting these DB
boundaries (one `CLIENT`/`INTERNAL` span + an outcome counter per query) is the
main remaining telemetry improvement.

## Verify Telemetry

```bash
# Start Jaeger, exercise tools, check trace tree
dagger call verify-telemetry --source=.
```

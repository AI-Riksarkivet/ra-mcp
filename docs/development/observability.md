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

The SDK sets `service.name`, `service.version`, a per-process
`service.instance.id`, and — when `ENVIRONMENT` is set —
`deployment.environment.name` as resource attributes; `OTEL_RESOURCE_ATTRIBUTES`
is merged on top.

`service.instance.id` defaults to a fresh UUID per process so replicas are
distinguishable (the chart autoscales to several pods). To pin a **stable**
per-pod id, set it from the Kubernetes downward API:

```yaml
env:
  - name: POD_NAME
    valueFrom: { fieldRef: { fieldPath: metadata.name } }
  - name: OTEL_RESOURCE_ATTRIBUTES
    value: "service.instance.id=$(POD_NAME)"
```

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
| LanceDB spine | `ra_mcp.lancedb` | `search <table>` (CLIENT) — all 13 datasets + PDF-guide search | `ra_mcp.lancedb.queries`, `ra_mcp.lancedb.errors`, `ra_mcp.lancedb.query.duration`, `ra_mcp.lancedb.results` |
| TORA geocoding | `ra_mcp.tora.client` | `tora sparql` (CLIENT) | — |
| PDF cache | `ra_mcp.pdf.cache` | `fetch pdf range` (CLIENT), `prefetch pdf` (INTERNAL) | — |
| CLI commands | `ra_mcp.cli.*` | `cli.search`, `cli.browse` | — |

FastMCP adds automatic spans for all `tools/call` and `resources/read` operations.
Handlers enrich the current tool-call span with behavioural intent (search terms
via `db.query.text`, `view.reference_code`, `pdf.url`, `geocode.place`) and mark
it `ERROR` via `mark_span_error` when they return an error string instead of
raising — see [Behavioural analytics](analytics.md) for the product-question map.

Custom metrics all declare a UCUM unit (`s`, `By`, or an annotation such as
`{request}` / `{fetch}` / `{page}`); metric dimensions are kept low-cardinality
(method, status, result enums), while per-request identifiers (URLs, PIDs,
reference codes, keywords, session ids) live on spans only.

## Error recording

Failures set `span.set_status(ERROR, "{ErrorClass}: …")` and record `error.type`
+ a structured `exception.*` log record via `record_span_exception()` — the OTel
Span Event API (`record_exception`) is deprecated, and the log record carries the
active `trace_id`/`span_id` through the log bridge. The stacktrace is logged once
per exception even as it unwinds through several layers (the counter isn't
inflated). Retried-then-succeeded requests stay `UNSET`.

A tool handler that catches an exception (or fails input validation) and returns
an error **string** instead of raising calls `mark_span_error(message,
error_type=…)` first, so the FastMCP `tools/call` span goes `ERROR` — otherwise a
normal return leaves it green and the tool failure rate reads zero.

## Verify Telemetry

```bash
# Start Jaeger, exercise tools, check trace tree
dagger call verify-telemetry --source=.
```

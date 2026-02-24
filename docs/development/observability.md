# Observability

Telemetry is gated on `RA_MCP_OTEL_ENABLED=true`. When enabled, traces, metrics, and logs are exported via OTLP.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RA_MCP_OTEL_ENABLED` | `false` | Master switch |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Collector endpoint |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc` | `grpc` or `http/protobuf` |
| `OTEL_SERVICE_NAME` | `ra-mcp` | Service name |
| `RA_MCP_OTEL_LOG_BRIDGE` | `true` | Bridge Python logging to OTel |

## Trace Tree

Every MCP tool call produces a trace spanning from the protocol layer down to HTTP:

``` mermaid
graph TD
  A["tools/call search_transcribed\n<i>FastMCP — automatic</i>"]
  B["delegate search_transcribed\n<i>FastMCP — composed server</i>"]
  C["tools/call search_transcribed\n<i>FastMCP — provider</i>"]
  D["SearchOperations.search\n<i>domain layer</i>"]
  E["SearchAPI.search\n<i>API client</i>"]
  F["HTTP GET\n<i>HTTP client</i>"]

  A --> B --> C --> D --> E --> F
```

## Instrumented Components

| Component | Tracer name | Spans | Metrics |
|-----------|-------------|-------|---------|
| HTTP client | `ra_mcp.http_client` | `HTTP GET` | request count, error count, duration, response size |
| Search API | `ra_mcp.search_api` | `SearchAPI.search` | — |
| Search ops | `ra_mcp.search_operations` | `SearchOperations.search` | — |
| Browse ops | `ra_mcp.browse_operations` | `browse_document`, `_fetch_page_contexts` | — |
| ALTO client | `ra_mcp.alto_client` | `ALTOClient.fetch_content` | — |
| IIIF client | `ra_mcp.iiif_client` | `IIIFClient.get_collection` | — |
| OAI-PMH client | `ra_mcp.oai_pmh_client` | `get_record`, `get_metadata` | — |
| CLI commands | `ra_mcp.cli.*` | `cli.search`, `cli.browse` | — |

FastMCP adds automatic spans for all `tools/call` and `resources/read` operations.

## Verify Telemetry

```bash
# Start Jaeger, exercise tools, check trace tree
dagger call verify-telemetry --source=.
```

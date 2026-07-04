# Behavioural analytics from OTEL

ra-mcp's OpenTelemetry isn't only for ops health — it's instrumented so you can
answer **product questions**: what people search for, which datasets and features
they use, and what they want but can't find. This page maps those questions to the
spans and metrics that answer them.

Enable it with `RA_MCP_OTEL_ENABLED=true` and point `OTEL_EXPORTER_OTLP_ENDPOINT`
at your collector (see [Observability](observability.md)). Traces carry the
high-cardinality *intent* (search terms, reference codes); metrics carry the
bounded *aggregates* (per-dataset counts, latencies) for dashboards and alerts.

## Where the signal lives (and why)

| Signal | Kind | Why |
|--------|------|-----|
| Search term, filter, reference code | **span attribute** | High-cardinality — belongs on sampled traces, never on a metric label (which must stay bounded). |
| Per-dataset counts, result distribution, latency | **metric** | Bounded labels (dataset name) — safe to aggregate into dashboards/SLOs. |
| Failures + stacktraces | **span status + correlated log** | `record_span_exception` sets `error.type` on the span and emits a trace-correlated ERROR log. |

## Questions you can answer

### "What are people searching for?"
Every search records the term on a span:

- **Datasets + PDF guides** → `search <dataset>` span, attribute **`db.query.text`** (the term), **`db.query.filter`** (filters applied, e.g. `gender = 'm'`), **`db.response.total_hits`** (how well the data answered). Covers all 13 datasets and the guide search (both go through the shared spine).
- **Live archive search** → `SearchOperations.search` span, attributes **`search.keyword`**, `search.total_hits`, `search.offset`.

Query your trace store for these span attributes to see the actual terms, grouped by dataset.

### "What do people open, view, and geocode?"
Searching is only half of intent — what users then *open* is the other half:

- **Viewer** → `view_document` / `viewer_navigate` spans, attributes **`view.reference_code`** (which archive document) and **`view.pages`**.
- **PDF viewer** → `display_pdf` span, attribute **`pdf.url`** (which guide/PDF).
- **Geocoding** → `tora search` spans, attributes **`geocode.place`** (+ `geocode.parish` / `geocode.county`) — which historical places people look up.

### "Which datasets / features are most used?"
- **`ra_mcp.lancedb.queries`** counter, by **`db.collection.name`** → per-dataset (and guide) search volume.
- **`ra_mcp.search.requests`** counter, by `search.type` → live transcribed vs metadata search volume.
- Tool popularity (which viewer, which tool) → the FastMCP `tools/call` spans (one per tool); derive per-tool counts in the collector (`spanmetricsconnector`).

### "What do people want but can't find?" (unmet demand)
This is the highest-value product signal:

- **`ra_mcp.lancedb.results`** histogram, by `db.collection.name` → its **zero bucket** is the rate of searches that returned nothing, per dataset.
- Then read the **`db.query.text`** of those zero-hit spans (`db.response.total_hits = 0`) to see the *actual* terms people searched for that your data doesn't answer — a direct backlog of data/feature gaps.

### "How engaged are they?"
- `search.offset` (span) → how deep users paginate.
- `ra_mcp.browse.pages` / `ra_mcp.browse.empty_pages` → pages read per browse, and blank-page rate.
- `db.response.total_hits` vs `db.response.returned_rows` → corpus richness vs page shown.

### "The research funnel: search → browse → view"
Search spans carry **`mcp.session.id`** (when the client sends it); correlate spans within a session/trace to see whether a search led to a browse and then a document/PDF view.

### "Which upstream is slow or failing?"
- **`ra_mcp.http.request.duration`** / **`ra_mcp.http.errors`** now carry **`server.address`** → per-upstream RED (Solr API vs IIIF vs OAI-PMH vs HF CDN), not one blurred series.
- LanceDB: **`ra_mcp.lancedb.query.duration`** + **`ra_mcp.lancedb.errors`** by dataset.

## Coverage at a glance

| Surface | Term captured | Volume metric | Result/latency metric | Failures |
|---------|:---:|:---:|:---:|:---:|
| Dataset search (×13) | ✅ span | ✅ by dataset | ✅ results + duration | ✅ span+log+counter |
| PDF guide search | ✅ span | ✅ | ✅ | ✅ |
| Live archive search | ✅ span | ✅ by type | ✅ results | ✅ |
| Browse | ref code on span | ✅ | pages / empty pages + duration | ✅ |
| Viewer open | ✅ `view.reference_code` + `view.pages` | via spanmetrics | — | FastMCP span |
| PDF open | ✅ `pdf.url` | via spanmetrics | — | FastMCP span |
| Geocoding (tora) | ✅ `geocode.place` (+parish/county) | via spanmetrics | — | ✅ span+log |
| HTR | tool span | via spanmetrics | — | ✅ log |

> Terms and reference codes are user intent, exposed only in traces (sampled, access-controlled), never in metric labels. Treat your trace/log backend accordingly.

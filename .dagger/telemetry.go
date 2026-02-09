package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"time"
)

// Jaeger API response types
type jaegerResponse struct {
	Data []jaegerTrace `json:"data"`
}

type jaegerTrace struct {
	TraceID string       `json:"traceID"`
	Spans   []jaegerSpan `json:"spans"`
}

type jaegerSpan struct {
	SpanID        string      `json:"spanID"`
	OperationName string      `json:"operationName"`
	References    []jaegerRef `json:"references"`
	StartTime     int64       `json:"startTime"` // microseconds
	Duration      int64       `json:"duration"`  // microseconds
	Tags          []jaegerTag `json:"tags"`
}

type jaegerRef struct {
	RefType string `json:"refType"`
	SpanID  string `json:"spanID"`
}

type jaegerTag struct {
	Key   string      `json:"key"`
	Type  string      `json:"type"`
	Value interface{} `json:"value"`
}

type spanNode struct {
	span     *jaegerSpan
	children []*spanNode
}

// parseTraces unmarshals the Jaeger JSON response into traces.
func parseTraces(jsonStr string) ([]jaegerTrace, error) {
	var resp jaegerResponse
	if err := json.Unmarshal([]byte(jsonStr), &resp); err != nil {
		return nil, err
	}
	return resp.Data, nil
}

// buildTraceTree converts a flat list of spans into a tree of root nodes.
func buildTraceTree(t jaegerTrace) []*spanNode {
	nodes := make(map[string]*spanNode, len(t.Spans))
	for i := range t.Spans {
		nodes[t.Spans[i].SpanID] = &spanNode{span: &t.Spans[i]}
	}

	var roots []*spanNode
	for _, node := range nodes {
		parentID := ""
		for _, ref := range node.span.References {
			if ref.RefType == "CHILD_OF" {
				parentID = ref.SpanID
				break
			}
		}
		if parentID != "" {
			if parent, ok := nodes[parentID]; ok {
				parent.children = append(parent.children, node)
				continue
			}
		}
		roots = append(roots, node)
	}

	// Sort children by start time at every level
	var sortChildren func(nodes []*spanNode)
	sortChildren = func(nodes []*spanNode) {
		for _, n := range nodes {
			sort.Slice(n.children, func(i, j int) bool {
				return n.children[i].span.StartTime < n.children[j].span.StartTime
			})
			sortChildren(n.children)
		}
	}
	sort.Slice(roots, func(i, j int) bool {
		return roots[i].span.StartTime < roots[j].span.StartTime
	})
	sortChildren(roots)

	return roots
}

// renderTraceTree renders a tree of span nodes with box-drawing characters.
func renderTraceTree(roots []*spanNode, indent string) string {
	var sb strings.Builder
	for _, root := range roots {
		renderNode(&sb, root, "")
	}
	return sb.String()
}

// selectedAttrs are the span attributes to display on each tree line.
var selectedAttrs = []string{
	"search.keyword",
	"browse.reference_code",
	"http.request.method",
	"http.response.status_code",
	"http.url",
}

func renderNode(sb *strings.Builder, node *spanNode, prefix string) {
	durationMs := node.span.Duration / 1000
	attrs := formatSelectedAttrs(node.span.Tags)

	line := fmt.Sprintf("%s [%dms]", node.span.OperationName, durationMs)
	if attrs != "" {
		line += "  " + attrs
	}
	sb.WriteString(prefix + line + "\n")

	for i, child := range node.children {
		isLast := i == len(node.children)-1
		connector := "├── "
		childPrefix := "│   "
		if isLast {
			connector = "└── "
			childPrefix = "    "
		}
		renderChild(sb, child, prefix+connector, prefix+childPrefix)
	}
}

func renderChild(sb *strings.Builder, node *spanNode, firstPrefix string, restPrefix string) {
	durationMs := node.span.Duration / 1000
	attrs := formatSelectedAttrs(node.span.Tags)

	line := fmt.Sprintf("%s [%dms]", node.span.OperationName, durationMs)
	if attrs != "" {
		line += "  " + attrs
	}
	sb.WriteString(firstPrefix + line + "\n")

	for i, child := range node.children {
		isLast := i == len(node.children)-1
		connector := "├── "
		childPrefix := "│   "
		if isLast {
			connector = "└── "
			childPrefix = "    "
		}
		renderChild(sb, child, restPrefix+connector, restPrefix+childPrefix)
	}
}

func formatSelectedAttrs(tags []jaegerTag) string {
	var parts []string
	for _, attrKey := range selectedAttrs {
		for _, tag := range tags {
			if tag.Key == attrKey {
				val := fmt.Sprintf("%v", tag.Value)
				if attrKey == "http.url" && len(val) > 50 {
					val = val[:50] + "..."
				}
				parts = append(parts, fmt.Sprintf("%s=%s", tag.Key, val))
				break
			}
		}
	}
	return strings.Join(parts, "  ")
}

// VerifyTelemetry spins up Jaeger, runs CLI commands with OTel enabled,
// then queries Jaeger's API to confirm traces were exported correctly.
func (m *RaMcp) VerifyTelemetry(
	ctx context.Context,
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
) (string, error) {
	// 1. Start Jaeger v2 as a Dagger service (native OTLP support)
	//    - Port 4317: OTLP gRPC receiver
	//    - Port 4318: OTLP HTTP receiver
	//    - Port 16686: Jaeger UI / Query API
	jaeger := dag.Container().
		From("jaegertracing/jaeger:latest").
		WithExposedPort(4317).
		WithExposedPort(4318).
		WithExposedPort(16686).
		AsService()

	// 2. Build a dev container with full source (same approach as test.go)
	appContainer := dag.Container().
		From("python:3.12-alpine").
		WithFile("/usr/local/bin/uv", dag.Container().From("ghcr.io/astral-sh/uv:0.5.13").File("/uv")).
		WithFile("/usr/local/bin/uvx", dag.Container().From("ghcr.io/astral-sh/uv:0.5.13").File("/uvx")).
		WithWorkdir("/app").
		WithDirectory("/app", source, dagger.ContainerWithDirectoryOpts{
			Include: []string{
				"pyproject.toml",
				"uv.lock",
				"packages/",
				"src/",
				"resources/",
				"assets/",
				"README.md",
				"LICENSE",
			},
		}).
		WithExec([]string{"uv", "sync", "--frozen", "--no-cache"})

	// Bind Jaeger service — do NOT set OTEL_EXPORTER_OTLP_ENDPOINT as env var
	// because Dagger rewrites env vars containing service hostnames to tunnel
	// addresses, which breaks port-specific routing. Instead, pass the endpoint
	// directly to the OTLPSpanExporter constructor in the Python script.
	appContainer = appContainer.
		WithServiceBinding("jaeger", jaeger).
		// Bust cache so the script always runs
		WithEnvVariable("CACHE_BUST", time.Now().String())

	// 3. Wait for Jaeger to be ready, then run search + browse
	//    Uses SimpleSpanProcessor for synchronous export (no batch timing issues)
	//    Passes endpoint directly to exporter to avoid Dagger env var rewriting
	verifyScript := `
import sys, os, time, urllib.request
sys.path.insert(0, '/app/src')

JAEGER_OTLP_HTTP = "http://jaeger:4318"
JAEGER_QUERY = "http://jaeger:16686"

# Wait for Jaeger to be ready
for i in range(30):
    try:
        urllib.request.urlopen(f"{JAEGER_QUERY}/api/services", timeout=2)
        print(f"Jaeger ready after {i+1} attempts", file=sys.stderr)
        break
    except Exception:
        time.sleep(1)
else:
    print("WARNING: Jaeger not ready after 30s", file=sys.stderr)

# Test OTLP HTTP connectivity before setting up the exporter
try:
    req = urllib.request.Request(f"{JAEGER_OTLP_HTTP}/v1/traces", method="POST",
        data=b"", headers={"Content-Type": "application/x-protobuf"})
    resp = urllib.request.urlopen(req, timeout=5)
    print(f"OTLP endpoint reachable: {resp.status}", file=sys.stderr)
except Exception as e:
    # 400/415 is expected (empty body), but proves connectivity
    print(f"OTLP endpoint test: {e}", file=sys.stderr)

# Set up OTel with SimpleSpanProcessor for synchronous (immediate) export
# Pass endpoint directly to exporter — avoids Dagger env var rewriting
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

resource = Resource.create({"service.name": "ra-mcp"})
provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint=f"{JAEGER_OTLP_HTTP}/v1/traces")
provider.add_span_processor(SimpleSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

print(f"TracerProvider configured with endpoint={JAEGER_OTLP_HTTP}/v1/traces", file=sys.stderr)

# Run instrumented code — all spans export synchronously as they complete
from ra_mcp_common.utils.http_client import default_http_client
from ra_mcp_search.operations import SearchOperations
from ra_mcp_browse.operations import BrowseOperations
from ra_mcp_common.telemetry import get_tracer

tracer = get_tracer("ra_mcp.cli.search")
with tracer.start_as_current_span("cli.search", attributes={"search.keyword": "Stockholm"}):
    ops = SearchOperations(http_client=default_http_client)
    result = ops.search(keyword="Stockholm", max_results=2)
    print(f"Search: {result.response.total_hits} hits", file=sys.stderr)

tracer2 = get_tracer("ra_mcp.cli.browse")
with tracer2.start_as_current_span("cli.browse", attributes={"browse.reference_code": "SE/RA/310187/1", "browse.pages": "7"}):
    bops = BrowseOperations(http_client=default_http_client)
    bresult = bops.browse_document(reference_code="SE/RA/310187/1", pages="7")
    print(f"Browse: {len(bresult.contexts)} pages", file=sys.stderr)

provider.force_flush(timeout_millis=10000)
provider.shutdown()
print("All spans exported", file=sys.stderr)
`

	appContainer = appContainer.WithExec(
		[]string{"uv", "run", "python", "-c", verifyScript},
	)

	// 4. Wait for Jaeger to ingest spans
	appContainer = appContainer.WithExec([]string{"sleep", "5"})

	// 5. Query Jaeger API for services
	servicesOutput, err := appContainer.WithExec(
		[]string{"sh", "-c", "wget -qO- 'http://jaeger:16686/api/services' 2>/dev/null || echo '{}'"},
	).Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to query Jaeger services: %w", err)
	}

	// 6. Query Jaeger API for traces from ra-mcp service
	tracesOutput, err := appContainer.WithExec(
		[]string{"sh", "-c", "wget -qO- 'http://jaeger:16686/api/traces?service=ra-mcp&limit=10' 2>/dev/null || echo '{}'"},
	).Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to query Jaeger traces: %w", err)
	}

	// 7. Validate results
	var results []string
	results = append(results, "=== OpenTelemetry Verification ===\n")

	// Check service registration
	if strings.Contains(servicesOutput, "ra-mcp") {
		results = append(results, "✅ Service 'ra-mcp' registered in Jaeger")
	} else {
		results = append(results, fmt.Sprintf("❌ Service 'ra-mcp' NOT found in Jaeger\n   Services response: %s", servicesOutput))
	}

	// Check traces exist
	if strings.Contains(tracesOutput, "traceID") {
		results = append(results, "✅ Traces found in Jaeger")
	} else {
		results = append(results, fmt.Sprintf("❌ No traces found in Jaeger\n   Traces response: %.500s", tracesOutput))
	}

	// Check for expected span names
	expectedSpans := []struct {
		name  string
		label string
	}{
		{"cli.search", "CLI search span"},
		{"SearchOperations.search", "Search operations span"},
		{"SearchAPI.search", "Search API client span"},
		{"HTTP GET", "HTTP client span"},
		{"cli.browse", "CLI browse span"},
		{"BrowseOperations.browse_document", "Browse operations span"},
		{"OAIPMHClient", "OAI-PMH client span"},
	}

	for _, expected := range expectedSpans {
		if strings.Contains(tracesOutput, expected.name) {
			results = append(results, fmt.Sprintf("✅ %s (%s)", expected.label, expected.name))
		} else {
			results = append(results, fmt.Sprintf("⚠️  %s not found (%s)", expected.label, expected.name))
		}
	}

	// Check for expected attributes
	expectedAttrs := []struct {
		attr  string
		label string
	}{
		{"search.keyword", "Search keyword attribute"},
		{"http.request.method", "HTTP method attribute"},
		{"http.response.status_code", "HTTP status code attribute"},
		{"browse.reference_code", "Browse reference code attribute"},
	}

	results = append(results, "")
	for _, expected := range expectedAttrs {
		if strings.Contains(tracesOutput, expected.attr) {
			results = append(results, fmt.Sprintf("✅ %s (%s)", expected.label, expected.attr))
		} else {
			results = append(results, fmt.Sprintf("⚠️  %s not found (%s)", expected.label, expected.attr))
		}
	}

	// Summary
	results = append(results, "\n=== Summary ===")
	if strings.Contains(servicesOutput, "ra-mcp") && strings.Contains(tracesOutput, "traceID") {
		results = append(results, "✅ OpenTelemetry integration verified successfully!")
	} else {
		results = append(results, "❌ OpenTelemetry verification had issues - check details above")
	}

	// Parse and display trace trees
	traces, err := parseTraces(tracesOutput)
	if err == nil && len(traces) > 0 {
		results = append(results, "\n=== Trace Trees ===\n")
		for i, t := range traces {
			roots := buildTraceTree(t)
			results = append(results, fmt.Sprintf("Trace %d:", i+1))
			results = append(results, renderTraceTree(roots, ""))
		}
	}

	return strings.Join(results, "\n"), nil
}

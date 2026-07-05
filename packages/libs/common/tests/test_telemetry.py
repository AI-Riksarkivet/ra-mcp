"""Telemetry behaviour tests using an in-memory OTel span exporter.

Proves, without a live collector, that:
- the project's canonical error-recording pattern sets span status ERROR with a
  message carrying the exception class, and
- ``record_span_exception`` emits a structured ``exception.*`` log record, and
- the shared ``HTTPClient`` emits a CLIENT ``HTTP GET`` span.
"""

import logging

import httpx
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_common.telemetry import get_tracer, mark_exception_logged, mark_span_error, record_span_exception


logger = logging.getLogger("ra_mcp.test.telemetry")


@pytest.fixture(scope="module")
def _exporter() -> InMemorySpanExporter:
    """Route the global tracer provider through an in-memory exporter.

    RA_MCP_OTEL_ENABLED is unset under test, so the global provider is the API
    no-op proxy; install a real SDK provider once. If a real provider is already
    installed, attach the exporter to it instead of fighting the set-once rule.
    """
    exporter = InMemorySpanExporter()
    current = trace.get_tracer_provider()
    if isinstance(current, TracerProvider):
        current.add_span_processor(SimpleSpanProcessor(exporter))
    else:
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    return exporter


@pytest.fixture
def spans(_exporter):
    _exporter.clear()
    yield _exporter
    _exporter.clear()


def test_error_span_carries_status_error_and_error_class(spans):
    tracer = get_tracer("ra_mcp.test")

    with tracer.start_as_current_span("op") as span:
        try:
            raise ValueError("boom")
        except ValueError as exc:
            span.set_status(StatusCode.ERROR, f"{type(exc).__name__}: {exc}")
            record_span_exception(logger, exc)

    finished = spans.get_finished_spans()
    assert [s.name for s in finished] == ["op"]
    assert finished[0].status.status_code == StatusCode.ERROR
    assert finished[0].status.description == "ValueError: boom"


def test_ok_span_defaults_to_unset_status(spans):
    tracer = get_tracer("ra_mcp.test")

    with tracer.start_as_current_span("healthy"):
        pass

    finished = spans.get_finished_spans()
    assert finished[0].status.status_code == StatusCode.UNSET


def test_record_span_exception_emits_structured_exception_log(caplog):
    with caplog.at_level(logging.ERROR, logger="ra_mcp.test.telemetry"):
        try:
            raise RuntimeError("kaboom")
        except RuntimeError as exc:
            record_span_exception(logger, exc)

    record = caplog.records[-1]
    assert record.__dict__["exception.type"] == "RuntimeError"
    assert record.__dict__["exception.message"] == "kaboom"
    assert "RuntimeError: kaboom" in record.__dict__["exception.stacktrace"]


def test_record_span_exception_logs_once_per_exception(spans, caplog):
    # The same exception unwinding through several layers must log its stacktrace
    # ONCE (not once per layer), while still marking error.type on each span.
    tracer = get_tracer("ra_mcp.test")
    with caplog.at_level(logging.ERROR, logger="ra_mcp.test.telemetry"):
        try:
            raise RuntimeError("kaboom")
        except RuntimeError as exc:
            with tracer.start_as_current_span("inner"):
                record_span_exception(logger, exc)  # origin — logs
            with tracer.start_as_current_span("outer"):
                record_span_exception(logger, exc)  # pass-through — marks only

    assert sum(1 for r in caplog.records if r.name == "ra_mcp.test.telemetry") == 1
    finished = {s.name: s for s in spans.get_finished_spans()}
    assert finished["inner"].attributes["error.type"] == "RuntimeError"
    assert finished["outer"].attributes["error.type"] == "RuntimeError"


def test_mark_exception_logged_suppresses_relog_of_wrapper(spans, caplog):
    # When an inner layer records an exception and then wraps it in a NEW exception
    # before re-raising (httpx timeout -> TimeoutError), marking the wrapper keeps the
    # outer layers from logging the same failure a second time.
    tracer = get_tracer("ra_mcp.test")
    with caplog.at_level(logging.ERROR, logger="ra_mcp.test.telemetry"):
        try:
            raise ValueError("inner timeout")
        except ValueError as exc:
            with tracer.start_as_current_span("inner"):
                record_span_exception(logger, exc)  # origin — logs once
            wrapper = TimeoutError("Request timeout")
            mark_exception_logged(wrapper)
            with tracer.start_as_current_span("outer"):
                record_span_exception(logger, wrapper)  # pre-marked — marks span only

    assert sum(1 for r in caplog.records if r.name == "ra_mcp.test.telemetry") == 1
    assert spans.get_finished_spans()[-1].attributes["error.type"] == "TimeoutError"


def test_mark_span_error_sets_status_and_type_without_logging(spans, caplog):
    # A handler that returns an error string (never raises) must still turn the
    # active span red — otherwise the tools/call failure rate reads zero.
    tracer = get_tracer("ra_mcp.test")
    with caplog.at_level(logging.ERROR, logger="ra_mcp.test.telemetry"), tracer.start_as_current_span("tool"):
        mark_span_error("keyword must not be empty", error_type="validation")

    span = spans.get_finished_spans()[0]
    assert span.status.status_code == StatusCode.ERROR
    assert span.status.description == "keyword must not be empty"
    assert span.attributes["error.type"] == "validation"
    assert not [r for r in caplog.records if r.name == "ra_mcp.test.telemetry"]


@pytest.mark.respx(base_url="https://data.example.se")
async def test_http_client_emits_client_span_named_http_get(spans, respx_mock):
    respx_mock.get("/api/records").mock(return_value=httpx.Response(200, json={"ok": True}))

    client = HTTPClient()
    try:
        await client.get_json("https://data.example.se/api/records")
    finally:
        await client.aclose()

    http_spans = [s for s in spans.get_finished_spans() if s.name == "HTTP GET"]
    assert http_spans, "HTTPClient did not emit an 'HTTP GET' span"
    assert http_spans[0].kind == SpanKind.CLIENT

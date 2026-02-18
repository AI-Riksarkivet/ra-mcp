"""
OpenTelemetry SDK initialization for ra-mcp.

Configures TracerProvider, MeterProvider, and LoggerProvider with OTLP exporters.
Gated on RA_MCP_OTEL_ENABLED=true — does nothing when disabled.

Environment variables:
    RA_MCP_OTEL_ENABLED: Master switch (default: false)
    OTEL_EXPORTER_OTLP_ENDPOINT: Collector endpoint (default: http://localhost:4317)
    OTEL_EXPORTER_OTLP_PROTOCOL: grpc or http/protobuf (default: grpc)
    OTEL_SERVICE_NAME: Service name (default: ra-mcp)
    RA_MCP_OTEL_LOG_BRIDGE: Bridge Python logging to OTel (default: true)
"""

import logging
import os


_initialized = False
_providers: list = []

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    return os.getenv("RA_MCP_OTEL_ENABLED", "false").lower() in ("true", "1", "yes")


def init_telemetry() -> None:
    """Initialize OpenTelemetry SDK if RA_MCP_OTEL_ENABLED is set.

    Safe to call multiple times — only initializes once.
    """
    global _initialized
    if _initialized or not _is_enabled():
        return

    from opentelemetry import metrics, trace
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    from ra_mcp_server import __version__

    service_name = os.getenv("OTEL_SERVICE_NAME", "ra-mcp")
    resource = Resource.create({"service.name": service_name, "service.version": __version__})

    protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")

    if protocol == "http/protobuf":
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    else:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    # Traces
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)
    _providers.append(tracer_provider)

    # Metrics
    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    _providers.append(meter_provider)

    # Build-info gauge (Prometheus _info pattern: value=1 with version label)
    meter = metrics.get_meter("ra_mcp")
    build_info = meter.create_gauge("ra_mcp.build_info", description="Build information for the ra-mcp server")
    build_info.set(1, {"version": __version__})

    # Log message counter (by severity level)
    log_counter = meter.create_counter("ra_mcp.log.messages", description="Log messages emitted by severity level")
    _setup_log_metrics(log_counter)

    # Log bridge
    if os.getenv("RA_MCP_OTEL_LOG_BRIDGE", "true").lower() in ("true", "1", "yes"):
        _setup_log_bridge(resource)

    _initialized = True
    logger.info("OpenTelemetry initialized (service=%s, version=%s, protocol=%s)", service_name, __version__, protocol)


class _MetricsLoggingHandler(logging.Handler):
    """Logging handler that increments an OTel counter per log level."""

    def __init__(self, counter) -> None:
        super().__init__()
        self._counter = counter

    def emit(self, record: logging.LogRecord) -> None:
        self._counter.add(1, {"log.level": record.levelname})


def _setup_log_metrics(counter) -> None:
    """Attach a metrics handler to the root logger that counts messages by level."""
    handler = _MetricsLoggingHandler(counter)
    handler.setLevel(logging.WARNING)
    logging.getLogger().addHandler(handler)


def _setup_log_bridge(resource) -> None:
    """Attach OTel LoggingHandler to the Python root logger."""
    try:
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

        protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
        if protocol == "http/protobuf":
            from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        else:
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

        log_provider = LoggerProvider(resource=resource)
        log_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
        _providers.append(log_provider)

        handler = LoggingHandler(level=logging.NOTSET, logger_provider=log_provider)
        logging.getLogger().addHandler(handler)
    except Exception:
        logger.debug("OTel log bridge setup failed — continuing without log export", exc_info=True)


def shutdown_telemetry() -> None:
    """Flush and shut down all OTel providers. Safe to call even if not initialized."""
    for provider in _providers:
        try:
            if hasattr(provider, "force_flush"):
                provider.force_flush(timeout_millis=5000)
            provider.shutdown()
        except Exception:
            pass
    _providers.clear()

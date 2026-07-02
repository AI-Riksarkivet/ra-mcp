"""
Telemetry convenience wrappers using only opentelemetry-api.

Returns no-op instances when no SDK is configured (zero overhead).
All packages get these helpers transitively through ra-mcp-common.
"""

import logging
import traceback

from opentelemetry import metrics, trace


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for the given module name.

    Returns a no-op tracer when no TracerProvider SDK is configured.
    """
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter for the given module name.

    Returns a no-op meter when no MeterProvider SDK is configured.
    """
    return metrics.get_meter(name)


def record_span_exception(logger: logging.Logger, exc: BaseException) -> None:
    """Record an exception on the active span the OTel-recommended way.

    The Span Event API (``span.record_exception``) is being deprecated, so
    instead of attaching a span event we emit a structured log record carrying
    the ``exception.*`` fields. Emitted inside the active span context, the
    record automatically carries the current ``trace_id``/``span_id`` (via the
    OTel logging bridge) so it stays correlated with the failing span.

    Callers remain responsible for ``span.set_status(StatusCode.ERROR, ...)``;
    this helper only records the exception detail.
    """
    logger.error(
        "exception",
        extra={
            "exception.type": type(exc).__name__,
            "exception.message": str(exc),
            "exception.stacktrace": traceback.format_exc(),
        },
    )

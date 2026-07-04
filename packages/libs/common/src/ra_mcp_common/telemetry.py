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
    """Record an exception on the active span and in a correlated log record.

    The Span Event API (``span.record_exception``) is being deprecated, so instead
    of a span event this helper:

    1. sets the semantic-convention ``error.type`` attribute on the active span
       (so trace stores can group/filter by error class) — callers still set
       ``span.set_status(StatusCode.ERROR, ...)``; and
    2. emits a structured ERROR log. The exception class + message go in the log
       *message* (readable with the plain stdlib formatter, not only via the OTLP
       bridge), ``exc_info`` attaches the stacktrace, and the ``exception.*``
       extras stay for the bridge. Emitted inside the active span context, the
       record inherits the current ``trace_id``/``span_id``.
    """
    exc_type = type(exc).__name__
    trace.get_current_span().set_attribute("error.type", exc_type)
    logger.error(
        "%s: %s",
        exc_type,
        exc,
        exc_info=exc,
        extra={
            "exception.type": exc_type,
            "exception.message": str(exc),
            "exception.stacktrace": traceback.format_exc(),
        },
    )

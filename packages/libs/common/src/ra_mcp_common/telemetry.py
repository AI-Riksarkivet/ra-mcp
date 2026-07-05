"""
Telemetry convenience wrappers using only opentelemetry-api.

Returns no-op instances when no SDK is configured (zero overhead).
All packages get these helpers transitively through ra-mcp-common.
"""

import contextlib
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


_LOGGED_MARKER = "_ra_mcp_logged"


def record_span_exception(logger: logging.Logger, exc: BaseException) -> None:
    """Record an exception on the active span and in a correlated log record.

    The Span Event API (``span.record_exception``) is being deprecated, so instead
    of a span event this helper:

    1. sets the semantic-convention ``error.type`` attribute on the active span
       (so trace stores can group/filter by error class) — callers still set
       ``span.set_status(StatusCode.ERROR, ...)``; and
    2. emits a structured ERROR log **once per exception**. The exception class +
       message go in the log *message* (readable with the plain stdlib formatter,
       not only via the OTLP bridge), ``exc_info`` attaches the stacktrace, and the
       ``exception.*`` extras stay for the bridge. Emitted inside the active span
       context, the record inherits the current ``trace_id``/``span_id``.

    The ``error.type`` attribute is set on *every* span in the propagation path
    (that is how the trace tree shows which spans failed), but the stacktrace is
    logged only the first time this exception is seen — a single failure that
    unwinds through http_client -> search_client -> search_operations would
    otherwise emit the same traceback ~4x and inflate the ERROR-log counter ~4x.
    """
    exc_type = type(exc).__name__
    trace.get_current_span().set_attribute("error.type", exc_type)

    if getattr(exc, _LOGGED_MARKER, False):
        # Already logged at an inner layer as it propagated up — mark this span's
        # error.type (done above) but don't re-emit the same stacktrace.
        return
    # Some builtin/C exceptions forbid attribute assignment — log anyway if so.
    with contextlib.suppress(AttributeError, TypeError):
        object.__setattr__(exc, _LOGGED_MARKER, True)

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


def mark_exception_logged(exc: BaseException) -> None:
    """Mark ``exc`` as already logged so :func:`record_span_exception` won't re-emit
    its stacktrace.

    Use when an inner layer records an exception and then wraps it in a *new*
    exception before re-raising (e.g. httpx.TimeoutException -> TimeoutError):
    ``raise NewError(...) from exc`` only sets ``__cause__``, so the wrapper would
    otherwise look unseen and get its stacktrace logged a second time as it unwinds.
    """
    with contextlib.suppress(AttributeError, TypeError):
        object.__setattr__(exc, _LOGGED_MARKER, True)


def mark_span_error(message: str, error_type: str = "handled_error") -> None:
    """Mark the active span ERROR when a tool returns an error *string* rather
    than raising.

    FastMCP's ``tools/call`` span reports OK whenever a handler returns normally,
    so a handler that catches an exception (or fails input validation) and returns
    an error string leaves that span green — making the top-level tool failure
    rate read as zero. Call this immediately before returning such a string so the
    span reflects the failure. ``error_type`` groups the failure class (e.g.
    ``"validation"`` for bad arguments vs the default ``"handled_error"`` for a
    caught exception); for caught exceptions, also call
    :func:`record_span_exception` to log the stacktrace once.
    """
    span = trace.get_current_span()
    span.set_status(trace.StatusCode.ERROR, message)
    span.set_attribute("error.type", error_type)

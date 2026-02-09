"""
Telemetry convenience wrappers using only opentelemetry-api.

Returns no-op instances when no SDK is configured (zero overhead).
All packages get these helpers transitively through ra-mcp-common.
"""

from opentelemetry import trace, metrics


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

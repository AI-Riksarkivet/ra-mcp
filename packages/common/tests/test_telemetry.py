"""Tests for telemetry convenience wrappers."""

from opentelemetry import metrics, trace

from ra_mcp_common.telemetry import get_meter, get_tracer


def test_get_tracer_returns_tracer():
    tracer = get_tracer("test.module")
    assert isinstance(tracer, trace.Tracer)


def test_get_meter_returns_meter():
    meter = get_meter("test.module")
    assert isinstance(meter, metrics.Meter)


def test_get_tracer_different_names_return_tracers():
    t1 = get_tracer("module.a")
    t2 = get_tracer("module.b")
    assert isinstance(t1, trace.Tracer)
    assert isinstance(t2, trace.Tracer)


def test_get_meter_different_names_return_meters():
    m1 = get_meter("module.a")
    m2 = get_meter("module.b")
    assert isinstance(m1, metrics.Meter)
    assert isinstance(m2, metrics.Meter)

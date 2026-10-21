"""Tests for ra-mcp root OpenTelemetry setup."""

import logging

from ra_mcp_server import telemetry


class _Provider:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.shut_down = False

    def shutdown(self) -> None:
        if self.fail:
            raise RuntimeError("exporter unreachable")
        self.shut_down = True


def test_shutdown_telemetry_logs_failure_and_continues(monkeypatch, caplog) -> None:
    failing, healthy = _Provider(fail=True), _Provider()
    monkeypatch.setattr(telemetry, "_providers", [failing, healthy])

    with caplog.at_level(logging.DEBUG, logger=telemetry.logger.name):
        telemetry.shutdown_telemetry()

    assert healthy.shut_down
    assert telemetry._providers == []
    assert any(r.exc_info and "exporter unreachable" in str(r.exc_info[1]) for r in caplog.records)

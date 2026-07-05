"""Tests for the shared dev-server entrypoint (arg parsing + transport branch)."""

from unittest.mock import MagicMock

import pytest

from ra_mcp_common.dev_server import run_dev_server


def test_defaults_to_streamable_http_on_default_port(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog"])
    monkeypatch.delenv("PORT", raising=False)
    mcp = MagicMock()

    run_dev_server(mcp, description="X MCP Server", default_port=3009)

    mcp.run.assert_called_once_with(transport="streamable-http", host="0.0.0.0", port=3009, path="/mcp")


def test_stdio_flag_runs_over_stdio(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--stdio"])
    mcp = MagicMock()

    run_dev_server(mcp, description="X MCP Server", default_port=3009)

    mcp.run.assert_called_once_with(transport="stdio")


def test_port_flag_overrides_default(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog", "--port", "9999"])
    mcp = MagicMock()

    run_dev_server(mcp, description="X MCP Server", default_port=3009)

    assert mcp.run.call_args.kwargs["port"] == 9999


def test_env_port_used_when_no_flag(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog"])
    monkeypatch.setenv("PORT", "7777")
    mcp = MagicMock()

    run_dev_server(mcp, description="X MCP Server", default_port=3009)

    assert mcp.run.call_args.kwargs["port"] == 7777


@pytest.mark.parametrize("flag_port,env_port,expected", [("8000", "7000", 8000), ("8000", None, 8000)])
def test_flag_takes_precedence_over_env(monkeypatch, flag_port, env_port, expected):
    monkeypatch.setattr("sys.argv", ["prog", "--port", flag_port])
    if env_port:
        monkeypatch.setenv("PORT", env_port)
    mcp = MagicMock()

    run_dev_server(mcp, description="X MCP Server", default_port=3009)

    assert mcp.run.call_args.kwargs["port"] == expected

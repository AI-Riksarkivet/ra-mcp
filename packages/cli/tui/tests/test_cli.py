"""Tests for the CLI entry point."""

from ra_mcp_tui.cli import tui_app


def test_tui_app_name():
    assert tui_app.info.name == "tui"


def test_tui_app_has_command():
    assert len(tui_app.registered_commands) > 0

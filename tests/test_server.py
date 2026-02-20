"""Tests for ra-mcp root server composition."""

from ra_mcp_server.server import AVAILABLE_MODULES


def test_available_modules_has_search() -> None:
    assert "search" in AVAILABLE_MODULES


def test_available_modules_has_browse() -> None:
    assert "browse" in AVAILABLE_MODULES


def test_available_modules_has_guide() -> None:
    assert "guide" in AVAILABLE_MODULES


def test_all_default_modules_have_server_key() -> None:
    for name, config in AVAILABLE_MODULES.items():
        assert "server" in config, f"Module '{name}' missing 'server' key"
        assert "description" in config, f"Module '{name}' missing 'description' key"
        assert "default" in config, f"Module '{name}' missing 'default' key"

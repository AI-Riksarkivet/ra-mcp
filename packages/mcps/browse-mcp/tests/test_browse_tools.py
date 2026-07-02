"""Tests for ra-mcp-browse-mcp tools."""

from ra_mcp_browse_mcp.tools import browse_mcp


def test_browse_mcp_has_name() -> None:
    assert browse_mcp.name == "ra-browse-mcp"

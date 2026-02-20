"""Tests for ra-mcp-guide-mcp tools."""

from ra_mcp_guide_mcp.tools import guide_mcp


def test_guide_mcp_has_name() -> None:
    assert guide_mcp.name == "ra-guide-mcp"

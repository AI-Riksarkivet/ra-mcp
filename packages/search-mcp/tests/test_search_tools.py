"""Tests for ra-mcp-search-mcp tools."""

from ra_mcp_search_mcp.tools import search_mcp


def test_search_mcp_has_name() -> None:
    assert search_mcp.name == "ra-search-mcp"

"""Tests for aktiebolag MCP server."""

from ra_mcp_aktiebolag_mcp import aktiebolag_mcp


def test_aktiebolag_mcp_server_name():
    assert aktiebolag_mcp.name == "ra-aktiebolag-mcp"

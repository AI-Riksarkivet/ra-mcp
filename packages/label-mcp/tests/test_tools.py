"""Tests for ra_mcp_label_mcp.tools (server setup)."""

from ra_mcp_label_mcp.tools import label_mcp


def test_label_mcp_has_name():
    assert label_mcp.name == "ra-label-mcp"


def test_label_mcp_has_instructions():
    assert label_mcp.instructions
    assert "import_to_label_studio" in label_mcp.instructions

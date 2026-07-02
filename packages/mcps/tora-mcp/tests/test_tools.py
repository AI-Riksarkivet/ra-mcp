"""Basic tests for the tora-mcp package."""


def test_tora_mcp_has_name():
    from ra_mcp_tora_mcp.tools import tora_mcp

    assert tora_mcp.name == "ra-tora-mcp"

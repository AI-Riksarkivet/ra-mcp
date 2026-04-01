"""Basic tests for the wincars-mcp package."""


def test_wincars_mcp_has_name():
    from ra_mcp_wincars_mcp.tools import wincars_mcp

    assert wincars_mcp.name == "ra-wincars-mcp"

"""Basic tests for the diplomatics-mcp package."""


def test_diplomatics_mcp_has_name():
    from ra_mcp_diplomatics_mcp.tools import diplomatics_mcp

    assert diplomatics_mcp.name == "ra-diplomatics-mcp"

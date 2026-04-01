"""Basic tests for the filmcensur-mcp package."""


def test_filmcensur_mcp_has_name():
    from ra_mcp_filmcensur_mcp.tools import filmcensur_mcp

    assert filmcensur_mcp.name == "ra-filmcensur-mcp"

"""Basic tests for the sbl-mcp package."""


def test_sbl_mcp_has_name():
    from ra_mcp_sbl_mcp.tools import sbl_mcp

    assert sbl_mcp.name == "ra-sbl-mcp"

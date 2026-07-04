"""Basic tests for the sj-mcp package."""


def test_sj_mcp_has_name():
    from ra_mcp_sj_mcp.tools import sj_mcp

    assert sj_mcp.name == "ra-sj-mcp"

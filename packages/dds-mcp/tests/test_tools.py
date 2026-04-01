"""Basic tests for the dds-mcp package."""


def test_dds_mcp_has_name():
    from ra_mcp_dds_mcp.tools import dds_mcp

    assert dds_mcp.name == "ra-dds-mcp"

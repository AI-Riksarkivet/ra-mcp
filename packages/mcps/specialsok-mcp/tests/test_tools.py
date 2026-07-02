"""Basic tests for the specialsok-mcp package."""


def test_specialsok_mcp_has_name():
    from ra_mcp_specialsok_mcp.tools import specialsok_mcp

    assert specialsok_mcp.name == "ra-specialsok-mcp"

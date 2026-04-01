"""Basic tests for the court-mcp package."""


def test_court_mcp_has_name():
    from ra_mcp_court_mcp.tools import court_mcp

    assert court_mcp.name == "ra-court-mcp"

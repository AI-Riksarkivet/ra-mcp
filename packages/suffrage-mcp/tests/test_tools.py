"""Basic tests for the suffrage-mcp package."""


def test_suffrage_mcp_has_name():
    from ra_mcp_suffrage_mcp.tools import suffrage_mcp

    assert suffrage_mcp.name == "ra-suffrage-mcp"

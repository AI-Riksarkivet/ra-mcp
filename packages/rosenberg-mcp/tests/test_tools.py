"""Basic tests for the rosenberg-mcp package."""


def test_rosenberg_mcp_has_name():
    from ra_mcp_rosenberg_mcp.tools import rosenberg_mcp

    assert rosenberg_mcp.name == "ra-rosenberg-mcp"

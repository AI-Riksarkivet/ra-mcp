"""Basic tests for the sjomanshus-mcp package."""


def test_sjomanshus_mcp_has_name():
    from ra_mcp_sjomanshus_mcp.tools import sjomanshus_mcp

    assert sjomanshus_mcp.name == "ra-sjomanshus-mcp"

"""In-memory ``Client`` smoke test for the guide-mcp MCP server (resources)."""

from fastmcp import Client

from ra_mcp_guide_mcp import guide_mcp


async def test_guide_mcp_exposes_expected_resource():
    async with Client(guide_mcp) as client:
        uris = {str(r.uri) for r in await client.list_resources()}

    assert "riksarkivet://contents/table_of_contents" in uris

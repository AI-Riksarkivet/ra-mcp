"""In-memory ``Client`` smoke test for the browse-mcp MCP server.

Verifies the server composes and every registered tool is a well-formed MCP
tool definition (name, description, input schema) — the FastMCP-recommended
first line of defence against registration/schema regressions.
"""

from fastmcp import Client

from ra_mcp_browse_mcp import browse_mcp


async def test_browse_mcp_registers_expected_tools():
    async with Client(browse_mcp) as client:
        tools = await client.list_tools()

    names = {t.name for t in tools}
    assert "document" in names


async def test_browse_mcp_tools_are_well_formed():
    async with Client(browse_mcp) as client:
        tools = await client.list_tools()

    assert tools, "server registered no tools"
    for tool in tools:
        assert tool.description, f"{tool.name} has no description"
        assert tool.inputSchema is not None, f"{tool.name} has no input schema"

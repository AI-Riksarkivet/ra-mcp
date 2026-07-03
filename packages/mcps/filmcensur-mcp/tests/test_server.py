"""In-memory ``Client`` smoke test for the filmcensur-mcp MCP server.

Verifies the server composes and every registered tool is a well-formed MCP
tool definition (name, description, input schema) — the FastMCP-recommended
first line of defence against registration/schema regressions.
"""

from fastmcp import Client

from ra_mcp_filmcensur_mcp import filmcensur_mcp


async def test_filmcensur_mcp_registers_expected_tools():
    async with Client(filmcensur_mcp) as client:
        tools = await client.list_tools()

    names = {t.name for t in tools}
    assert "search_filmreg" in names


async def test_filmcensur_mcp_tools_are_well_formed():
    async with Client(filmcensur_mcp) as client:
        tools = await client.list_tools()

    assert tools, "server registered no tools"
    for tool in tools:
        assert tool.description, f"{tool.name} has no description"
        assert tool.inputSchema is not None, f"{tool.name} has no input schema"

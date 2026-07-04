"""In-memory ``Client`` smoke test for the pdf-mcp MCP server.

Verifies the server composes and every registered tool is a well-formed MCP
tool definition (name, description, input schema) — the FastMCP-recommended
first line of defence against registration/schema regressions.
"""

from fastmcp import Client

from ra_mcp_pdf_mcp import pdf_mcp


async def test_pdf_mcp_registers_expected_tools():
    async with Client(pdf_mcp) as client:
        tools = await client.list_tools()

    names = {t.name for t in tools}
    assert "display_pdf" in names


async def test_pdf_mcp_tools_are_well_formed():
    async with Client(pdf_mcp) as client:
        tools = await client.list_tools()

    assert tools, "server registered no tools"
    for tool in tools:
        assert tool.description, f"{tool.name} has no description"
        assert tool.inputSchema is not None, f"{tool.name} has no input schema"

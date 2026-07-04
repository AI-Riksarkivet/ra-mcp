"""In-memory ``Client`` smoke test for the label-mcp MCP server.

label-mcp depends on label-studio-sdk (opencv), which has no musl wheel, so the
test skips cleanly when that optional dependency is not installed.
"""

import pytest


pytest.importorskip("label_studio_sdk")

from fastmcp import Client

from ra_mcp_label_mcp import label_mcp


async def test_label_mcp_registers_import_tool():
    async with Client(label_mcp) as client:
        names = {t.name for t in await client.list_tools()}

    assert "import_to_label_studio" in names

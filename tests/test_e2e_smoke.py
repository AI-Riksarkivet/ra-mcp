"""End-to-end smoke: the root server composes, registers modules, and serves
the viewer/pdf ui:// resources through one composed FastMCP — the wiring the unit
suite exercises piecemeal, checked here end to end.
"""

import pytest
from fastmcp import Client

from ra_mcp_server.server import create_server, setup_server


# Always-on modules only — no dataset data / network needed to register + serve.
CORE = ["search", "browse", "guide", "viewer", "pdf"]


@pytest.fixture
def server():
    srv = create_server(CORE)
    setup_server(srv, CORE)
    return srv


async def test_server_composes_and_exposes_core_tools(server):
    async with Client(server) as client:
        tools = {t.name for t in await client.list_tools()}
    # viewer + pdf mount without a namespace, so their entry tools are bare.
    assert "view_document" in tools
    assert "display_pdf" in tools
    assert "search_guides" in tools  # the new LanceDB-backed guide search
    # search mounts under a namespace; be robust to the separator.
    assert any("transcribed" in t for t in tools), tools


async def test_viewer_and_pdf_ui_resources_serve(server):
    async with Client(server) as client:
        resources = {str(r.uri) for r in await client.list_resources()}
        assert "ui://document-viewer/mcp-app.html" in resources
        assert "ui://pdf-viewer/mcp-app.html" in resources
        # the ui:// resource returns the built single-file app HTML
        result = await client.read_resource("ui://pdf-viewer/mcp-app.html")
        text = result[0].text
        assert "<" in text and len(text) > 1000

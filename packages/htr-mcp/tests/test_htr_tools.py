"""Smoke tests for the HTR MCP tool registration."""

from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client

from ra_mcp_htr_mcp.tools import htr_mcp


@pytest.mark.anyio
async def test_htr_transcribe_tool_is_registered():
    """Verify the htr_transcribe tool is discoverable via MCP."""
    async with Client(htr_mcp) as client:
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        assert "htr_transcribe" in tool_names


@pytest.mark.anyio
async def test_htr_transcribe_calls_gradio_client():
    """Verify htr_transcribe delegates to gradio_client.Client.predict."""
    mock_result = {
        "viewer_url": "https://example.com/viewer",
        "pages_url": "https://example.com/pages.json",
        "export_url": "https://example.com/export.xml",
        "export_format": "alto_xml",
    }

    mock_client = MagicMock()
    mock_client.predict.return_value = mock_result

    with patch("ra_mcp_htr_mcp.tools._get_client", return_value=mock_client):
        async with Client(htr_mcp) as client:
            result = await client.call_tool(
                "htr_transcribe",
                {"image_urls": ["https://example.com/image.jpg"]},
            )
            content = result.content[0].text
            assert "viewer_url" in content

    mock_client.predict.assert_called_once_with(
        image_urls=["https://example.com/image.jpg"],
        language="swedish",
        layout="single_page",
        export_format="alto_xml",
        custom_yaml=None,
        api_name="/htr_transcribe",
    )

"""Smoke tests for the HTR MCP tool registration."""

from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from ra_mcp_htr_mcp.tools import htr_mcp


@pytest.mark.anyio
async def test_htr_transcribe_tool_is_registered():
    """Verify the htr_transcribe tool is discoverable via MCP."""
    async with Client(htr_mcp) as client:
        tools = await client.list_tools()
        tool_names = [t.name for t in tools]
        assert "htr_transcribe" in tool_names


@pytest.mark.anyio
async def test_htr_transcribe_tool_has_annotations():
    """Verify MCP annotations are set on the tool."""
    async with Client(htr_mcp) as client:
        tools = await client.list_tools()
        tool = next(t for t in tools if t.name == "htr_transcribe")
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.openWorldHint is True


@pytest.mark.anyio
async def test_htr_transcribe_has_output_schema():
    """Verify the tool exposes a structured output schema."""
    async with Client(htr_mcp) as client:
        tools = await client.list_tools()
        tool = next(t for t in tools if t.name == "htr_transcribe")
        assert tool.outputSchema is not None
        props = tool.outputSchema.get("properties", {})
        assert "viewer_url" in props
        assert "pages_url" in props
        assert "export_url" in props


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


@pytest.mark.anyio
async def test_htr_transcribe_returns_structured_content():
    """Verify structured output is returned alongside text content."""
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
            assert result.structured_content is not None
            assert result.structured_content["viewer_url"] == "https://example.com/viewer"
            assert result.structured_content["export_format"] == "alto_xml"


@pytest.mark.anyio
async def test_htr_transcribe_predict_error_raises_tool_error():
    """Verify gradio_client errors are surfaced as ToolError."""
    mock_client = MagicMock()
    mock_client.predict.side_effect = RuntimeError("Space is sleeping")

    with patch("ra_mcp_htr_mcp.tools._get_client", return_value=mock_client):
        async with Client(htr_mcp) as client:
            with pytest.raises(ToolError, match="HTR transcription failed"):
                await client.call_tool(
                    "htr_transcribe",
                    {"image_urls": ["https://example.com/image.jpg"]},
                )

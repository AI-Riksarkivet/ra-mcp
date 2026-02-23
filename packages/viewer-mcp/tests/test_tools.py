"""Integration tests for MCP tools using FastMCP's in-memory test client."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from src import mcp

FIXTURES = Path(__file__).resolve().parent / "fixtures"

FAKE_IMAGE_DATA_URL = "data:image/jpeg;base64,/9j/fakedata"
FAKE_THUMBNAIL_DATA_URL = "data:image/jpeg;base64,/9j/thumbdata"


@pytest.fixture()
def alto_text_layer() -> dict:
    """A realistic parsed text layer dict from the ALTO fixture."""
    from src.parser import parse_alto_xml

    xml = (FIXTURES / "451511_1512_01_alto.xml").read_text()
    data = parse_alto_xml(xml)
    return {
        "textLines": [line.model_dump() for line in data.text_lines],
        "pageWidth": data.page_width,
        "pageHeight": data.page_height,
    }


@pytest.fixture()
def mock_fetchers(alto_text_layer):
    """Patch all async fetchers to avoid real HTTP calls."""
    with (
        patch("src.tools.fetch_and_parse_text_layer", new_callable=AsyncMock) as mock_text,
        patch("src.tools.build_page_data", new_callable=AsyncMock) as mock_page,
        patch("src.tools.fetch_thumbnail_as_data_url", new_callable=AsyncMock) as mock_thumb,
    ):
        mock_text.return_value = alto_text_layer
        mock_page.return_value = (
            {"index": 0, "imageDataUrl": FAKE_IMAGE_DATA_URL, "textLayer": alto_text_layer},
            [],
        )
        mock_thumb.return_value = FAKE_THUMBNAIL_DATA_URL
        yield {"text_layer": mock_text, "page": mock_page, "thumbnail": mock_thumb}


# ── view-document ─────────────────────────────────────────────────────


async def test_view_document_returns_transcription(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view-document",
            {
                "image_urls": ["https://example.com/img1.jpg"],
                "text_layer_urls": ["https://example.com/alto1.xml"],
            },
        )

    assert not result.is_error
    text = result.content[0].text
    assert "1-page document" in text
    assert "Mommouth" in text


async def test_view_document_mismatched_urls(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view-document",
            {
                "image_urls": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
                "text_layer_urls": ["https://example.com/alto1.xml"],
            },
        )

    text = result.content[0].text
    assert "mismatched" in text.lower()


# ── load-page ─────────────────────────────────────────────────────────


async def test_load_page_returns_structured_content(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "load-page",
            {
                "image_url": "https://example.com/img.jpg",
                "text_layer_url": "https://example.com/alto.xml",
                "page_index": 0,
            },
        )

    assert not result.is_error
    page = result.structured_content["page"]
    assert page["index"] == 0
    assert "imageDataUrl" in page
    assert "textLayer" in page
    assert isinstance(page["textLayer"]["textLines"], list)


# ── load-thumbnails ──────────────────────────────────────────────────


async def test_load_thumbnails_returns_list(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "load-thumbnails",
            {
                "image_urls": ["https://example.com/t1.jpg", "https://example.com/t2.jpg"],
                "page_indices": [0, 1],
            },
        )

    assert not result.is_error
    thumbnails = result.structured_content["thumbnails"]
    assert len(thumbnails) == 2
    assert thumbnails[0]["index"] == 0
    assert thumbnails[1]["index"] == 1
    assert all(t["dataUrl"].startswith("data:image/jpeg;base64,") for t in thumbnails)


# ── Error handling ───────────────────────────────────────────────────


async def test_load_page_handles_fetch_error():
    """Bad URL should produce an error in the page data, not crash the tool."""
    with patch("src.tools.build_page_data", new_callable=AsyncMock) as mock_page:
        mock_page.return_value = (
            {"index": 0, "imageDataUrl": "", "textLayer": {"textLines": [], "pageWidth": 0, "pageHeight": 0}},
            ["Page 1 image: connection refused"],
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "load-page",
                {
                    "image_url": "https://bad-url.example.com/img.jpg",
                    "text_layer_url": "",
                    "page_index": 0,
                },
            )

    assert not result.is_error
    assert "Errors" in result.content[0].text

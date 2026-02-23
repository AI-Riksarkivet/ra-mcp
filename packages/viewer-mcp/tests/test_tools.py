"""Integration tests for MCP tools using FastMCP's in-memory test client."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from ra_mcp_viewer_mcp import viewer_mcp as mcp


FIXTURES = Path(__file__).resolve().parent / "fixtures"

FAKE_IMAGE_DATA_URL = "data:image/jpeg;base64,/9j/fakedata"
FAKE_THUMBNAIL_DATA_URL = "data:image/jpeg;base64,/9j/thumbdata"


@pytest.fixture()
def alto_text_layer() -> dict:
    """A realistic parsed text layer dict from the ALTO fixture."""
    from ra_mcp_viewer_mcp.parser import parse_alto_xml

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
        patch("ra_mcp_viewer_mcp.tools.fetch_and_parse_text_layer", new_callable=AsyncMock) as mock_text,
        patch("ra_mcp_viewer_mcp.tools.build_page_data", new_callable=AsyncMock) as mock_page,
        patch("ra_mcp_viewer_mcp.tools.fetch_thumbnail_as_data_url", new_callable=AsyncMock) as mock_thumb,
    ):
        mock_text.return_value = alto_text_layer
        mock_page.return_value = (
            {"index": 0, "imageDataUrl": FAKE_IMAGE_DATA_URL, "textLayer": alto_text_layer},
            [],
        )
        mock_thumb.return_value = FAKE_THUMBNAIL_DATA_URL
        yield {"text_layer": mock_text, "page": mock_page, "thumbnail": mock_thumb}


# ── view_document ─────────────────────────────────────────────────────


async def test_view_document_returns_transcription(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {
                "image_urls": ["https://example.com/img1.jpg"],
                "text_layer_urls": ["https://example.com/alto1.xml"],
            },
        )

    assert not result.is_error
    text = result.content[0].text
    assert "1-page document" in text
    assert "Mommouth" in text


async def test_view_document_with_highlight_term(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {
                "image_urls": ["https://example.com/img1.jpg"],
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "highlight_term": "Stockholm",
                "highlight_term_color": "#ef4444",
            },
        )

    assert not result.is_error
    text = result.content[0].text
    assert "1-page document" in text


async def test_view_document_mismatched_urls(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {
                "image_urls": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
                "text_layer_urls": ["https://example.com/alto1.xml"],
            },
        )

    text = result.content[0].text
    assert "mismatched" in text.lower()


# ── load_page ─────────────────────────────────────────────────────────


async def test_load_page_returns_structured_content(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "load_page",
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


# ── load_thumbnails ──────────────────────────────────────────────────


async def test_load_thumbnails_returns_list(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "load_thumbnails",
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
    with patch("ra_mcp_viewer_mcp.tools.build_page_data", new_callable=AsyncMock) as mock_page:
        mock_page.return_value = (
            {"index": 0, "imageDataUrl": "", "textLayer": {"textLines": [], "pageWidth": 0, "pageHeight": 0}},
            ["Page 1 image: connection refused"],
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "load_page",
                {
                    "image_url": "https://bad-url.example.com/img.jpg",
                    "text_layer_url": "",
                    "page_index": 0,
                },
            )

    assert not result.is_error
    assert "Errors" in result.content[0].text


# ── search_all_pages ─────────────────────────────────────────────────


async def test_search_all_pages_returns_matches(mock_fetchers):
    """Searching for a term that exists in the fixture text layer should return matches."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml", "https://example.com/alto2.xml"],
                "term": "Mommouth",
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] > 0
    assert len(sc["pageMatches"]) > 0
    for m in sc["pageMatches"]:
        assert "pageIndex" in m
        assert "matchCount" in m
        assert m["matchCount"] > 0


async def test_search_all_pages_no_matches(mock_fetchers):
    """Searching for a term not in the fixture should return zero matches."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "term": "xyznonexistentterm",
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] == 0
    assert sc["pageMatches"] == []


async def test_search_all_pages_empty_term(mock_fetchers):
    """Empty search term should return early with zero matches."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "term": "",
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] == 0
    assert sc["pageMatches"] == []


async def test_search_all_pages_skips_empty_urls(mock_fetchers):
    """Empty string URLs should be skipped without error."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["", "https://example.com/alto1.xml", ""],
                "term": "Mommouth",
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] > 0
    # Only the valid URL (index 1) should appear in matches
    page_indices = [m["pageIndex"] for m in sc["pageMatches"]]
    assert 0 not in page_indices  # empty URL skipped
    assert 1 in page_indices


async def test_search_all_pages_case_insensitive(mock_fetchers):
    """Search should be case-insensitive."""
    async with Client(mcp) as client:
        result_lower = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "term": "mommouth",
            },
        )
        result_upper = await client.call_tool(
            "search_all_pages",
            {
                "text_layer_urls": ["https://example.com/alto1.xml"],
                "term": "MOMMOUTH",
            },
        )

    assert result_lower.structured_content["totalMatches"] == result_upper.structured_content["totalMatches"]
    assert result_lower.structured_content["totalMatches"] > 0

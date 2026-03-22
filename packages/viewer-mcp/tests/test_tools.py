"""Integration tests for MCP tools using FastMCP's in-memory test client."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from ra_mcp_browse_lib.models import BrowseResult, PageContext
from ra_mcp_viewer_mcp import viewer_mcp as mcp
import ra_mcp_viewer_mcp.tools as _tools_mod


FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def _reset_viewer_state():
    """Reset server-side viewer state between tests."""
    _tools_mod._viewer_state.update(
        version=0, image_urls=[], text_layer_urls=[], page_numbers=[], highlight_term="", reference_code="",
    )
    yield
    _tools_mod._viewer_state.update(
        version=0, image_urls=[], text_layer_urls=[], page_numbers=[], highlight_term="", reference_code="",
    )

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
def fake_browse_result() -> BrowseResult:
    """A fake BrowseResult with one page context."""
    return BrowseResult(
        contexts=[
            PageContext(
                page_number=7,
                page_id="7",
                reference_code="SE/RA/310187/1",
                full_text="skäligt sin emillan förafskeda, och det eftter Kongl. Mommouth",
                alto_url="https://sok.riksarkivet.se/dokument/alto/R000/R0001203/R0001203_00007.xml",
                image_url="https://lbiiif.riksarkivet.se/arkis!R0001203_00007/full/max/0/default.jpg",
                bildvisning_url="https://sok.riksarkivet.se/bildvisning/R0001203_00007",
            ),
        ],
        reference_code="SE/RA/310187/1",
        pages_requested="7",
        manifest_id="R0001203",
    )


@pytest.fixture()
def mock_fetchers(alto_text_layer, fake_browse_result):
    """Patch all async fetchers and BrowseOperations to avoid real HTTP calls."""
    with (
        patch("ra_mcp_viewer_mcp.tools.fetch_and_parse_text_layer", new_callable=AsyncMock) as mock_text,
        patch("ra_mcp_viewer_mcp.tools.build_page_data", new_callable=AsyncMock) as mock_page,
        patch("ra_mcp_viewer_mcp.tools.fetch_thumbnail_as_data_url", new_callable=AsyncMock) as mock_thumb,
        patch("ra_mcp_viewer_mcp.tools.BrowseOperations") as mock_browse_cls,
    ):
        mock_text.return_value = alto_text_layer
        mock_page.return_value = (
            {"index": 0, "imageDataUrl": FAKE_IMAGE_DATA_URL, "textLayer": alto_text_layer},
            [],
        )
        mock_thumb.return_value = FAKE_THUMBNAIL_DATA_URL
        mock_browse = AsyncMock()
        mock_browse.browse_document.return_value = fake_browse_result
        mock_browse_cls.return_value = mock_browse
        yield {"text_layer": mock_text, "page": mock_page, "thumbnail": mock_thumb, "browse": mock_browse}


# ── view_document ─────────────────────────────────────────────────────


async def test_view_document_returns_transcription(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {"reference_code": "SE/RA/310187/1", "pages": "7"},
        )

    assert not result.is_error
    text = result.content[0].text
    assert "1 page(s)" in text
    assert "Mommouth" in text
    assert result.structured_content["image_urls"]
    assert result.structured_content["text_layer_urls"]


async def test_view_document_with_highlight_term(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {"reference_code": "SE/RA/310187/1", "pages": "7", "highlight_term": "trolldom"},
        )

    assert not result.is_error
    assert result.structured_content["highlight_term"] == "trolldom"


async def test_view_document_empty_reference_code(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document",
            {"reference_code": "", "pages": "1"},
        )

    text = result.content[0].text
    assert "empty" in text.lower()


# ── get_viewer_state (polling) ────────────────────────────────────────


async def test_get_viewer_state_returns_version(mock_fetchers):
    """Calling view_document should update server state; get_viewer_state returns it."""
    async with Client(mcp) as client:
        # State starts at version 0
        result = await client.call_tool("get_viewer_state", {})
        assert not result.is_error
        assert result.structured_content["version"] == 0

        # Call view_document to bump state
        await client.call_tool(
            "view_document",
            {"reference_code": "SE/RA/310187/1", "pages": "7"},
        )

        # Poll should now return version 1 with the new data
        result = await client.call_tool("get_viewer_state", {})
        assert result.structured_content["version"] == 1
        assert len(result.structured_content["image_urls"]) == 1
        assert result.structured_content["reference_code"] == "SE/RA/310187/1"


async def test_get_viewer_state_updates_on_view_document_urls(mock_fetchers):
    """view_document_urls should also update the polling state."""
    async with Client(mcp) as client:
        await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/p1.jpg", "https://example.com/p2.jpg"],
                "text_layer_urls": ["https://example.com/p1.xml", ""],
            },
        )

        result = await client.call_tool("get_viewer_state", {})
        assert result.structured_content["version"] >= 1
        assert len(result.structured_content["image_urls"]) == 2
        assert result.structured_content["reference_code"] == ""


# ── viewer_set_highlight ──────────────────────────────────────────────


async def test_viewer_set_highlight_updates_state(mock_fetchers):
    """Setting highlight on an open viewer should bump version and update term."""
    async with Client(mcp) as client:
        # First open the viewer
        await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})

        # Then update highlight
        result = await client.call_tool("viewer_set_highlight", {"highlight_term": "trolldom"})

    assert not result.is_error
    assert "Highlighting" in result.content[0].text
    assert result.structured_content["highlight_term"] == "trolldom"
    assert result.structured_content["version"] == 2  # bumped from 1


async def test_viewer_set_highlight_without_viewer(mock_fetchers):
    """Setting highlight with no viewer open should error."""
    async with Client(mcp) as client:
        result = await client.call_tool("viewer_set_highlight", {"highlight_term": "test"})

    text = result.content[0].text
    assert "no document" in text.lower()


async def test_viewer_set_highlight_clear(mock_fetchers):
    """Empty string should clear highlights."""
    async with Client(mcp) as client:
        await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        result = await client.call_tool("viewer_set_highlight", {"highlight_term": ""})

    assert "Cleared" in result.content[0].text
    assert result.structured_content["highlight_term"] == ""


# ── viewer_navigate ──────────────────────────────────────────────────


async def test_viewer_navigate_updates_pages(mock_fetchers):
    """Navigating should update state with new pages."""
    async with Client(mcp) as client:
        await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        result = await client.call_tool("viewer_navigate", {"reference_code": "SE/RA/310187/1", "pages": "8"})

    assert not result.is_error
    assert "Navigated" in result.content[0].text
    assert result.structured_content["version"] == 2


async def test_viewer_navigate_with_highlight(mock_fetchers):
    async with Client(mcp) as client:
        await client.call_tool("view_document", {"reference_code": "SE/RA/310187/1", "pages": "7"})
        result = await client.call_tool(
            "viewer_navigate",
            {"reference_code": "SE/RA/310187/1", "pages": "7", "highlight_term": "Stockholm"},
        )

    assert result.structured_content["highlight_term"] == "Stockholm"


# ── viewer_navigate_urls ──────────────────────────────────────────────


async def test_viewer_navigate_urls_updates_pages(mock_fetchers):
    """Navigate with raw URLs should update state without creating new viewer."""
    async with Client(mcp) as client:
        await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/p1.jpg"],
                "text_layer_urls": ["https://example.com/p1.xml"],
            },
        )
        result = await client.call_tool(
            "viewer_navigate_urls",
            {
                "image_urls": ["https://example.com/p3.jpg", "https://example.com/p4.jpg"],
                "text_layer_urls": ["https://example.com/p3.xml", ""],
            },
        )

    assert not result.is_error
    assert "Navigated" in result.content[0].text
    assert result.structured_content["version"] == 2
    assert len(result.structured_content["image_urls"]) == 2


# ── view_document_urls ────────────────────────────────────────────────


async def test_view_document_urls_returns_structured_content(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": [
                    "https://lbiiif.riksarkivet.se/arkis!30002056_00010/full/max/0/default.jpg",
                    "https://lbiiif.riksarkivet.se/arkis!30002056_00011/full/max/0/default.jpg",
                ],
                "text_layer_urls": [
                    "https://sok.riksarkivet.se/dokument/alto/3000/30002056/30002056_00010.xml",
                    "https://sok.riksarkivet.se/dokument/alto/3000/30002056/30002056_00011.xml",
                ],
            },
        )

    assert not result.is_error
    text = result.content[0].text
    assert "2 page(s)" in text
    sc = result.structured_content
    assert len(sc["image_urls"]) == 2
    assert len(sc["text_layer_urls"]) == 2
    assert sc["page_numbers"] == [1, 2]
    assert sc["reference_code"] == ""


async def test_view_document_urls_with_highlight_term(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/page1.jpg"],
                "text_layer_urls": ["https://example.com/page1.xml"],
                "highlight_term": "trolldom",
            },
        )

    assert not result.is_error
    assert result.structured_content["highlight_term"] == "trolldom"


async def test_view_document_urls_mismatched_lengths(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/page1.jpg", "https://example.com/page2.jpg"],
                "text_layer_urls": ["https://example.com/page1.xml"],
            },
        )

    text = result.content[0].text
    assert "mismatched" in text.lower()


async def test_view_document_urls_empty_image_urls(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": [],
                "text_layer_urls": [],
            },
        )

    text = result.content[0].text
    assert "empty" in text.lower()


async def test_view_document_urls_with_empty_text_layers(mock_fetchers):
    """Pages without transcription should use empty string in text_layer_urls."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/p1.jpg", "https://example.com/p2.jpg"],
                "text_layer_urls": ["https://example.com/p1.xml", ""],
            },
        )

    assert not result.is_error
    sc = result.structured_content
    assert sc["text_layer_urls"][1] == ""


async def test_view_document_urls_metadata_length_mismatch(mock_fetchers):
    async with Client(mcp) as client:
        result = await client.call_tool(
            "view_document_urls",
            {
                "image_urls": ["https://example.com/p1.jpg"],
                "text_layer_urls": ["https://example.com/p1.xml"],
                "metadata": ["label1", "label2"],
            },
        )

    text = result.content[0].text
    assert "metadata length" in text.lower()


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

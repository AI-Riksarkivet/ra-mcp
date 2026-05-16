"""Integration tests for PDF MCP tools using FastMCP's in-memory test client."""

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from ra_mcp_pdf_mcp import pdf_mcp as mcp
from ra_mcp_pdf_mcp.cache import blocks_cache, pdf_cache
import ra_mcp_pdf_mcp.state as _state_mod


SAMPLE_URL = "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/test.pdf?download=true"

SAMPLE_PAGES = [
    {
        "page": 0,
        "bbox": [0, 0, 595, 842],
        "children": [
            {"html": "<p>Riksarkivets handlingar</p>", "bbox": [72, 100, 400, 130], "block_type": "SectionHeader"},
            {"html": "<p>Stockholm 1723</p>", "bbox": [72, 140, 400, 160], "block_type": "Text"},
        ],
    },
    {
        "page": 1,
        "bbox": [0, 0, 595, 842],
        "children": [
            {"html": "<p>Kapitel om trolldom och häxprocesser</p>", "bbox": [72, 100, 400, 130], "block_type": "Text"},
        ],
    },
]


# ── display_pdf ──────────────────────────────────────────────────────


async def test_display_pdf_returns_view_id():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            result = await client.call_tool("display_pdf", {"url": SAMPLE_URL})

    assert not result.is_error
    text = result.content[0].text
    assert "view_uuid:" in text
    assert result.structured_content["view_id"]
    assert result.structured_content["url"] == SAMPLE_URL


async def test_display_pdf_extracts_title_from_url():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            result = await client.call_tool("display_pdf", {"url": SAMPLE_URL})

    assert "test" in result.structured_content["title"].lower()


async def test_display_pdf_uses_custom_title():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            result = await client.call_tool("display_pdf", {"url": SAMPLE_URL, "title": "Custom Title"})

    assert result.structured_content["title"] == "Custom Title"


async def test_display_pdf_empty_url_returns_error():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            result = await client.call_tool("display_pdf", {"url": ""})

    text = result.content[0].text
    assert "Error" in text


# ── get_pdf_state ────────────────────────────────────────────────────


async def test_get_pdf_state_returns_stored_state():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            doc = await client.call_tool("display_pdf", {"url": SAMPLE_URL})
            view_id = doc.structured_content["view_id"]

            result = await client.call_tool("get_pdf_state", {"view_id": view_id})

    assert result.structured_content["version"] == 1
    assert result.structured_content["url"] == SAMPLE_URL


async def test_get_pdf_state_unknown_id_returns_defaults():
    async with Client(mcp) as client:
        result = await client.call_tool("get_pdf_state", {"view_id": "unknown-id"})

    assert result.structured_content["version"] == 0
    assert result.structured_content["url"] == ""


# ── pdf_set_search ───────────────────────────────────────────────────


async def test_pdf_set_search_updates_state():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            doc = await client.call_tool("display_pdf", {"url": SAMPLE_URL})
            view_id = doc.structured_content["view_id"]

            result = await client.call_tool("pdf_set_search", {"search_term": "trolldom"})

    assert not result.is_error
    assert "Highlighting" in result.content[0].text

    async with Client(mcp) as client:
        state = await client.call_tool("get_pdf_state", {"view_id": view_id})
    assert state.structured_content["search_term"] == "trolldom"


async def test_pdf_set_search_without_viewer_returns_error():
    async with Client(mcp) as client:
        result = await client.call_tool("pdf_set_search", {"search_term": "test"})

    text = result.content[0].text
    assert "Error" in text
    assert "display_pdf" in text.lower() or "viewer" in text.lower()


async def test_pdf_set_search_clear():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            await client.call_tool("display_pdf", {"url": SAMPLE_URL})
            result = await client.call_tool("pdf_set_search", {"search_term": ""})

    assert "Cleared" in result.content[0].text


# ── pdf_go_to_page ───────────────────────────────────────────────────


async def test_pdf_go_to_page_updates_state():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            doc = await client.call_tool("display_pdf", {"url": SAMPLE_URL})
            view_id = doc.structured_content["view_id"]

            result = await client.call_tool("pdf_go_to_page", {"page": 5})

    assert not result.is_error
    assert "page 5" in result.content[0].text.lower()

    async with Client(mcp) as client:
        state = await client.call_tool("get_pdf_state", {"view_id": view_id})
    assert state.structured_content["go_to_page"] == 4  # 0-based


async def test_pdf_go_to_page_without_viewer_returns_error():
    async with Client(mcp) as client:
        result = await client.call_tool("pdf_go_to_page", {"page": 1})

    text = result.content[0].text
    assert "Error" in text


# ── search_pdf ───────────────────────────────────────────────────────


async def test_search_pdf_finds_matches():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("search_pdf", {"url": SAMPLE_URL, "term": "Stockholm"})

    assert not result.is_error
    sc = result.structured_content
    assert sc["totalMatches"] >= 1
    assert len(sc["pageMatches"]) >= 1


async def test_search_pdf_no_matches():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("search_pdf", {"url": SAMPLE_URL, "term": "xyznonexistent"})

    sc = result.structured_content
    assert sc["totalMatches"] == 0
    assert sc["pageMatches"] == []


async def test_search_pdf_empty_term():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("search_pdf", {"url": SAMPLE_URL, "term": ""})

    sc = result.structured_content
    assert sc["totalMatches"] == 0


async def test_search_pdf_not_loaded():
    async with Client(mcp) as client:
        result = await client.call_tool("search_pdf", {"url": "https://example.com/missing.pdf", "term": "test"})

    text = result.content[0].text
    assert "Error" in text


# ── read_pdf_page ────────────────────────────────────────────────────


async def test_read_pdf_page_returns_text():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("read_pdf_page", {"url": SAMPLE_URL, "page": 1})

    assert not result.is_error
    text = result.content[0].text
    assert "Riksarkivets handlingar" in text
    assert "Page 1/" in text


async def test_read_pdf_page_multi_page():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("read_pdf_page", {"url": SAMPLE_URL, "page": 1, "count": 2})

    text = result.content[0].text
    assert "Page 1/" in text
    assert "Page 2/" in text
    assert "trolldom" in text


async def test_read_pdf_page_count_clamped_to_5():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("read_pdf_page", {"url": SAMPLE_URL, "page": 1, "count": 100})

    text = result.content[0].text
    assert "Page 1/" in text
    assert "Page 2/" in text


async def test_read_pdf_page_not_loaded():
    with patch("ra_mcp_pdf_mcp.cache.preload_all_guides", new_callable=AsyncMock):
        async with Client(mcp) as client:
            result = await client.call_tool("read_pdf_page", {"url": "https://example.com/missing.pdf", "page": 1})

    text = result.content[0].text
    assert "Error" in text


async def test_read_pdf_page_section_header_formatted():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("read_pdf_page", {"url": SAMPLE_URL, "page": 1})

    text = result.content[0].text
    assert "## Riksarkivets handlingar" in text


# ── get_page_blocks ──────────────────────────────────────────────────


async def test_get_page_blocks_returns_blocks():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("get_page_blocks", {"url": SAMPLE_URL, "page": 1})

    assert not result.is_error
    sc = result.structured_content
    assert "blocks" in sc
    assert len(sc["blocks"]) == 2
    assert sc["pageBbox"] == [0, 0, 595, 842]
    assert sc["blocks"][0]["blockType"] == "SectionHeader"


async def test_get_page_blocks_not_loaded():
    async with Client(mcp) as client:
        result = await client.call_tool("get_page_blocks", {"url": "https://x.com/missing.pdf", "page": 1})

    text = result.content[0].text
    assert "Error" in text


async def test_get_page_blocks_out_of_range():
    blocks_cache[SAMPLE_URL] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("get_page_blocks", {"url": SAMPLE_URL, "page": 99})

    text = result.content[0].text
    assert "Error" in text
    assert "out of range" in text.lower()


# ── list_pdfs ────────────────────────────────────────────────────────


async def test_list_pdfs_returns_gallery():
    async with Client(mcp) as client:
        result = await client.call_tool("list_pdfs", {})

    assert not result.is_error
    text = result.content[0].text
    assert "PDF guides available" in text
    sc = result.structured_content
    assert "items" in sc
    assert len(sc["items"]) > 0
    assert "url" in sc["items"][0]


# ── search_guides ────────────────────────────────────────────────────


async def test_search_guides_finds_across_multiple():
    from ra_mcp_pdf_mcp.gallery import GALLERY_ITEMS

    for item in GALLERY_ITEMS:
        blocks_cache[item["url"]] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("search_guides", {"term": "Stockholm"})

    assert not result.is_error
    text = result.content[0].text
    assert "matches" in text.lower()
    assert "Stockholm" in text


async def test_search_guides_empty_term():
    async with Client(mcp) as client:
        result = await client.call_tool("search_guides", {"term": ""})

    text = result.content[0].text
    assert "no search term" in text.lower()


async def test_search_guides_no_matches():
    from ra_mcp_pdf_mcp.gallery import GALLERY_ITEMS

    for item in GALLERY_ITEMS:
        blocks_cache[item["url"]] = SAMPLE_PAGES

    async with Client(mcp) as client:
        result = await client.call_tool("search_guides", {"term": "xyznonexistent123"})

    text = result.content[0].text
    assert "No matches" in text


# ── read_pdf_bytes ───────────────────────────────────────────────────


async def test_read_pdf_bytes_returns_base64():
    pdf_cache[SAMPLE_URL] = b"fake-pdf-content-1234567890"

    async with Client(mcp) as client:
        result = await client.call_tool("read_pdf_bytes", {"url": SAMPLE_URL, "offset": 0})

    assert not result.is_error
    sc = result.structured_content
    assert "bytes" in sc
    assert sc["offset"] == 0
    assert sc["byteCount"] > 0
    assert isinstance(sc["hasMore"], bool)


async def test_read_pdf_bytes_with_offset():
    data = b"A" * 100
    pdf_cache[SAMPLE_URL] = data

    async with Client(mcp) as client:
        result = await client.call_tool("read_pdf_bytes", {"url": SAMPLE_URL, "offset": 50})

    sc = result.structured_content
    assert sc["offset"] == 50
    assert sc["byteCount"] == 50


# ── Multi-view isolation ─────────────────────────────────────────────


async def test_multiple_display_pdf_creates_independent_views():
    with patch("ra_mcp_pdf_mcp.tools.schedule_prefetch"):
        async with Client(mcp) as client:
            doc_a = await client.call_tool("display_pdf", {"url": SAMPLE_URL, "title": "Doc A"})
            doc_b = await client.call_tool("display_pdf", {"url": SAMPLE_URL, "title": "Doc B"})

            view_a = doc_a.structured_content["view_id"]
            view_b = doc_b.structured_content["view_id"]
            assert view_a != view_b

            await client.call_tool("pdf_set_search", {"search_term": "latest"})

            state_a = await client.call_tool("get_pdf_state", {"view_id": view_a})
            state_b = await client.call_tool("get_pdf_state", {"view_id": view_b})

    assert state_a.structured_content["search_term"] == ""
    assert state_b.structured_content["search_term"] == "latest"

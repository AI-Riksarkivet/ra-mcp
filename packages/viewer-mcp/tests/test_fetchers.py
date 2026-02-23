"""Tests for async fetchers with mocked HTTP via respx."""

import base64
from pathlib import Path

import httpx
import pytest
import respx
from key_value.aio.stores.memory import MemoryStore

import src.fetchers as _fetchers_mod
from src.fetchers import (
    _http,
    build_page_data,
    fetch_and_parse_text_layer,
    fetch_image_as_data_url,
    fetch_thumbnail_as_data_url,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def _fresh_cache():
    """Swap in a fresh MemoryStore before each test."""
    original = _fetchers_mod._cache
    _fetchers_mod._cache = MemoryStore(max_entries_per_collection=128)
    yield
    _fetchers_mod._cache = original


@pytest.fixture()
def jpeg_bytes() -> bytes:
    return (FIXTURES / "451511_1512_01.jpg").read_bytes()


@pytest.fixture()
def alto_xml_text() -> str:
    return (FIXTURES / "451511_1512_01_alto.xml").read_text()


# ── Image fetch ───────────────────────────────────────────────────────


@respx.mock(assert_all_called=False)
async def test_fetch_image_returns_data_url(respx_mock, jpeg_bytes):
    url = "https://example.com/image.jpg"
    respx_mock.get(url).mock(
        return_value=httpx.Response(200, content=jpeg_bytes, headers={"content-type": "image/jpeg"})
    )

    result = await fetch_image_as_data_url(url)

    assert result.startswith("data:image/jpeg;base64,")
    decoded = base64.b64decode(result.split(",", 1)[1])
    assert decoded == jpeg_bytes


@respx.mock(assert_all_called=False)
async def test_fetch_image_cache_hit(respx_mock, jpeg_bytes):
    url = "https://example.com/cached-image.jpg"
    respx_mock.get(url).mock(
        return_value=httpx.Response(200, content=jpeg_bytes, headers={"content-type": "image/jpeg"})
    )

    first = await fetch_image_as_data_url(url)
    second = await fetch_image_as_data_url(url)

    assert first == second
    # Only one HTTP call should have been made
    assert respx_mock.calls.call_count == 1


# ── Thumbnail fetch ──────────────────────────────────────────────────


@respx.mock(assert_all_called=False)
async def test_fetch_thumbnail_resizes_and_caches(respx_mock, jpeg_bytes):
    url = "https://example.com/thumb.jpg"
    respx_mock.get(url).mock(
        return_value=httpx.Response(200, content=jpeg_bytes, headers={"content-type": "image/jpeg"})
    )

    result = await fetch_thumbnail_as_data_url(url)

    assert result.startswith("data:image/jpeg;base64,")
    # Thumbnail bytes should differ from original (resized + re-encoded)
    decoded = base64.b64decode(result.split(",", 1)[1])
    assert decoded != jpeg_bytes

    # Second call should be cached
    second = await fetch_thumbnail_as_data_url(url)
    assert second == result
    assert respx_mock.calls.call_count == 1


# ── Text layer fetch ─────────────────────────────────────────────────


@respx.mock(assert_all_called=False)
async def test_fetch_text_layer_parses_alto(respx_mock, alto_xml_text):
    url = "https://example.com/alto.xml"
    respx_mock.get(url).mock(
        return_value=httpx.Response(200, text=alto_xml_text, headers={"content-type": "application/xml"})
    )

    result = await fetch_and_parse_text_layer(url)

    assert "textLines" in result
    assert "pageWidth" in result
    assert "pageHeight" in result
    assert isinstance(result["textLines"], list)
    assert len(result["textLines"]) == 18
    assert result["pageWidth"] == 1511
    assert result["pageHeight"] == 2413

    # Cache hit
    second = await fetch_and_parse_text_layer(url)
    assert second == result
    assert respx_mock.calls.call_count == 1


# ── Cache TTL ─────────────────────────────────────────────────────────


async def test_cache_ttl_expiry():
    """Verify MemoryStore respects TTL — entry disappears after expiry."""
    store = MemoryStore(max_entries_per_collection=10)
    await store.put(key="key1", value={"value": 42}, collection="test_col", ttl=1)

    hit = await store.get(key="key1", collection="test_col")
    assert hit is not None
    assert hit["value"] == 42

    import asyncio

    await asyncio.sleep(1.1)

    miss = await store.get(key="key1", collection="test_col")
    assert miss is None


# ── build_page_data ──────────────────────────────────────────────────


@respx.mock(assert_all_called=False)
async def test_build_page_data(respx_mock, jpeg_bytes, alto_xml_text):
    img_url = "https://example.com/page.jpg"
    xml_url = "https://example.com/page.xml"
    respx_mock.get(img_url).mock(
        return_value=httpx.Response(200, content=jpeg_bytes, headers={"content-type": "image/jpeg"})
    )
    respx_mock.get(xml_url).mock(
        return_value=httpx.Response(200, text=alto_xml_text, headers={"content-type": "application/xml"})
    )

    page, errors = await build_page_data(0, img_url, xml_url)

    assert errors == []
    assert page["index"] == 0
    assert "imageDataUrl" in page
    assert page["imageDataUrl"].startswith("data:image/jpeg;base64,")
    assert "textLayer" in page
    assert len(page["textLayer"]["textLines"]) == 18


@respx.mock(assert_all_called=False)
async def test_build_page_data_empty_text_layer(respx_mock, jpeg_bytes):
    img_url = "https://example.com/page-no-text.jpg"
    respx_mock.get(img_url).mock(
        return_value=httpx.Response(200, content=jpeg_bytes, headers={"content-type": "image/jpeg"})
    )

    page, errors = await build_page_data(0, img_url, "")

    assert errors == []
    assert page["textLayer"]["textLines"] == []


# ── Connection reuse ─────────────────────────────────────────────────


def test_shared_async_client():
    """Verify the module exports a shared AsyncClient instance."""
    assert isinstance(_http, httpx.AsyncClient)
    assert _http._transport is not None

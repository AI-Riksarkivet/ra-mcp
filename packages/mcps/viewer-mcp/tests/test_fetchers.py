"""Tests for the async text-layer fetchers and the direct-URL page builder.

Images are no longer downloaded/base64-encoded server-side — build_page_data
returns a size-bounded IIIF URL for the browser to fetch directly.
"""

import asyncio
from pathlib import Path

import httpx
import pytest
import respx
from key_value.aio.stores.memory import MemoryStore

import ra_mcp_viewer_mcp.fetchers as _fetchers_mod
from ra_mcp_viewer_mcp.fetchers import (
    _http,
    build_page_data,
    fetch_and_parse_text_layer,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"
IIIF_URL = "https://lbiiif.riksarkivet.se/arkis!C0056829_00001/full/max/0/default.jpg"


@pytest.fixture(autouse=True)
def _fresh_cache():
    """Swap in a fresh text-layer MemoryStore before each test."""
    original = _fetchers_mod._cache
    _fetchers_mod._cache = MemoryStore(max_entries_per_collection=128)
    yield
    _fetchers_mod._cache = original


@pytest.fixture()
def alto_xml_text() -> str:
    return (FIXTURES / "451511_1512_01_alto.xml").read_text()


# ── Text layer fetch ─────────────────────────────────────────────────


@respx.mock(assert_all_called=False)
async def test_fetch_text_layer_parses_alto(respx_mock, alto_xml_text):
    url = "https://example.com/alto.xml"
    respx_mock.get(url).mock(return_value=httpx.Response(200, text=alto_xml_text, headers={"content-type": "application/xml"}))

    result = await fetch_and_parse_text_layer(url)

    assert "textLines" in result
    assert isinstance(result["textLines"], list)
    assert len(result["textLines"]) == 18
    assert result["pageWidth"] == 1511
    assert result["pageHeight"] == 2413

    # Cache hit — second call issues no new request
    second = await fetch_and_parse_text_layer(url)
    assert second == result
    assert respx_mock.calls.call_count == 1


@respx.mock(assert_all_called=False)
async def test_concurrent_same_url_dedups_to_one_request(respx_mock, alto_xml_text):
    url = "https://example.com/alto-concurrent.xml"
    respx_mock.get(url).mock(return_value=httpx.Response(200, text=alto_xml_text, headers={"content-type": "application/xml"}))

    # Two concurrent fetches for the same URL take the in-flight dedup path; both must
    # receive the parsed result from a single HTTP request (and the loser must not leak
    # an un-awaited coroutine — _dedup now takes a factory, not a live coroutine).
    r1, r2 = await asyncio.gather(
        fetch_and_parse_text_layer(url),
        fetch_and_parse_text_layer(url),
    )
    assert r1 == r2
    assert r1["pageWidth"] == 1511
    assert respx_mock.calls.call_count == 1


async def test_cache_ttl_expiry():
    """MemoryStore respects TTL — entry disappears after expiry."""
    store = MemoryStore(max_entries_per_collection=10)
    await store.put(key="key1", value={"value": 42}, collection="test_col", ttl=1)

    hit = await store.get(key="key1", collection="test_col")
    assert hit is not None and hit["value"] == 42

    await asyncio.sleep(1.1)

    assert await store.get(key="key1", collection="test_col") is None


# ── build_page_data (direct IIIF URL, no image download) ──────────────


@respx.mock(assert_all_called=False)
async def test_build_page_data_returns_bounded_iiif_url(respx_mock, alto_xml_text):
    xml_url = "https://example.com/page.xml"
    respx_mock.get(xml_url).mock(return_value=httpx.Response(200, text=alto_xml_text, headers={"content-type": "application/xml"}))
    img_route = respx_mock.get(IIIF_URL).mock(return_value=httpx.Response(200, content=b"x"))

    page, errors = await build_page_data(0, IIIF_URL, xml_url)

    assert errors == []
    assert page["index"] == 0
    assert page["imageDataUrl"] == "https://lbiiif.riksarkivet.se/arkis!C0056829_00001/full/1500,/0/default.jpg"
    assert not img_route.called, "image must be browser-fetched, not downloaded server-side"
    assert len(page["textLayer"]["textLines"]) == 18


async def test_build_page_data_empty_text_layer():
    page, errors = await build_page_data(0, IIIF_URL, "")

    assert errors == []
    assert page["textLayer"]["textLines"] == []
    assert page["imageDataUrl"].endswith("/full/1500,/0/default.jpg")


# ── Connection reuse ─────────────────────────────────────────────────


def test_shared_async_client():
    assert isinstance(_http, httpx.AsyncClient)
    assert _http._transport is not None

"""Architecture/perf tests: the viewer delivers page and thumbnail images as
size-bounded IIIF URLs the browser fetches directly, NOT as server-downloaded
base64 through the tool-result channel (MCP Apps external-URL delivery)."""

import asyncio
import time

import httpx
import pytest
import respx
from key_value.aio.stores.memory import MemoryStore

from ra_mcp_browse_lib.url_generator import iiif_resize
from ra_mcp_viewer_mcp.fetchers import build_page_data


IIIF_PAGE = "https://lbiiif.riksarkivet.se/arkis!C0056829_00001/full/max/0/default.jpg"


async def test_cache_get_is_fast():
    """MemoryStore get() (used for parsed text layers) is >5x faster than a fetch."""
    store = MemoryStore(max_entries_per_collection=128)
    await store.put(key="key", value={"data": "x" * 1000}, collection="bench", ttl=60)

    start = time.perf_counter()
    for _ in range(1000):
        await store.get(key="key", collection="bench")
    cache_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(10):
        await asyncio.sleep(0.001)
    fetch_time_per_call = (time.perf_counter() - start) / 10

    speedup = (fetch_time_per_call * 1000) / cache_time
    assert speedup > 5, f"Cache only {speedup:.1f}x faster than simulated fetch"


@pytest.mark.parametrize(
    "size,expected",
    [
        ("1500,", "https://lbiiif.riksarkivet.se/arkis!C0056829_00001/full/1500,/0/default.jpg"),
        ("150,", "https://lbiiif.riksarkivet.se/arkis!C0056829_00001/full/150,/0/default.jpg"),
    ],
)
def test_iiif_resize_bounds_the_size_segment(size, expected):
    assert iiif_resize(IIIF_PAGE, size) == expected


def test_iiif_resize_passes_non_iiif_urls_through():
    other = "https://example.com/image.png"
    assert iiif_resize(other, "150,") == other


@respx.mock(assert_all_called=False)
async def test_build_page_data_returns_bounded_url_without_downloading_image(respx_mock):
    """The page image is a bounded /full/1500,/ IIIF URL (not base64), and the
    server never downloads the scan — proving the base64 proxy path is gone."""
    image_route = respx_mock.get(IIIF_PAGE).mock(return_value=httpx.Response(200, content=b"x"))

    page, errors = await build_page_data(0, IIIF_PAGE, "")

    assert not errors
    assert page["imageDataUrl"] == "https://lbiiif.riksarkivet.se/arkis!C0056829_00001/full/1500,/0/default.jpg"
    assert not page["imageDataUrl"].startswith("data:"), "image must not be base64-inlined"
    assert not image_route.called, "server must not download the image; the browser fetches it directly"

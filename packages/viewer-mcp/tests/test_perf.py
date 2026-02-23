"""Performance benchmarks for caching and concurrent fetching."""

import asyncio
import time
from pathlib import Path

import httpx
import pytest
import respx
from key_value.aio.stores.memory import MemoryStore

import src.fetchers as _fetchers_mod
from src.fetchers import fetch_thumbnail_as_data_url

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


# ── Cache speed ───────────────────────────────────────────────────────


async def test_cache_get_is_fast():
    """MemoryStore get() should be >10x faster than a simulated fetch."""
    store = MemoryStore(max_entries_per_collection=128)
    await store.put(key="key", value={"data": "x" * 1000}, collection="bench", ttl=60)

    start = time.perf_counter()
    for _ in range(1000):
        await store.get(key="key", collection="bench")
    cache_time = time.perf_counter() - start

    # Simulate a "fetch" with a 1ms sleep
    start = time.perf_counter()
    for _ in range(10):
        await asyncio.sleep(0.001)
    fetch_time_per_call = (time.perf_counter() - start) / 10
    fetch_time_extrapolated = fetch_time_per_call * 1000

    speedup = fetch_time_extrapolated / cache_time
    assert speedup > 10, f"Cache only {speedup:.1f}x faster than simulated fetch"


# ── Concurrent fetching ──────────────────────────────────────────────


@respx.mock(assert_all_called=False)
async def test_concurrent_thumbnail_fetches(respx_mock, jpeg_bytes):
    """8 concurrent thumbnail fetches should complete in ~1x single-fetch time, not 8x."""
    delay = 0.05  # 50ms simulated latency per request

    async def _delayed_response(request):
        await asyncio.sleep(delay)
        return httpx.Response(200, content=jpeg_bytes, headers={"content-type": "image/jpeg"})

    urls = [f"https://example.com/thumb-{i}.jpg" for i in range(8)]
    for url in urls:
        respx_mock.get(url).mock(side_effect=_delayed_response)

    # Concurrent
    start = time.perf_counter()
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_thumbnail_as_data_url(url)) for url in urls]
    concurrent_time = time.perf_counter() - start

    # All should have returned valid data URLs
    for task in tasks:
        assert task.result().startswith("data:image/jpeg;base64,")

    # Concurrent time should be well under 8x sequential time
    sequential_estimate = delay * 8
    assert concurrent_time < sequential_estimate * 0.6, (
        f"Concurrent took {concurrent_time:.3f}s, sequential estimate {sequential_estimate:.3f}s"
    )

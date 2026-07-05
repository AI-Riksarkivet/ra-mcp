"""Tests for ra_mcp_pdf_mcp.cache — the bounded LRU cache and the range-fetch helpers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ra_mcp_pdf_mcp.cache import (
    MAX_PDF_SIZE,
    LRUCache,
    json_url_for,
    pdf_cache,
    read_pdf_range,
)


# ── LRUCache ─────────────────────────────────────────────────────────


def test_evicts_least_recently_used_over_item_bound():
    cache: LRUCache[int] = LRUCache(max_items=2)
    cache["a"] = 1
    cache["b"] = 2
    cache["c"] = 3  # evicts "a" (LRU)
    assert "a" not in cache
    assert "b" in cache
    assert "c" in cache
    assert len(cache) == 2


def test_access_refreshes_recency():
    cache: LRUCache[int] = LRUCache(max_items=2)
    cache["a"] = 1
    cache["b"] = 2
    _ = cache["a"]  # "a" is now most-recently-used
    cache["c"] = 3  # evicts "b", not "a"
    assert "a" in cache
    assert "b" not in cache


def test_byte_bound_evicts_when_total_exceeds():
    # Two 4-byte entries fit in 8 bytes; a third pushes the oldest out.
    cache: LRUCache[bytes] = LRUCache(max_items=100, max_bytes=8)
    cache["a"] = b"aaaa"
    cache["b"] = b"bbbb"
    cache["c"] = b"cccc"  # total would be 12 > 8 → evict "a"
    assert "a" not in cache
    assert "b" in cache
    assert "c" in cache


def test_reassigning_same_key_updates_byte_total():
    cache: LRUCache[bytes] = LRUCache(max_items=100, max_bytes=8)
    cache["a"] = b"aaaaaaaa"  # 8 bytes, exactly at bound
    cache["a"] = b"a"  # replace: total must drop to 1, not accumulate to 9
    cache["b"] = b"bbbb"  # 1 + 4 = 5 <= 8, both stay
    assert "a" in cache
    assert "b" in cache


def test_non_bytes_values_bound_by_count_only():
    # list values weigh 0 bytes, so a byte bound never evicts them; count does.
    cache: LRUCache[list] = LRUCache(max_items=2, max_bytes=1)
    cache["a"] = [1, 2, 3]
    cache["b"] = [4, 5, 6]
    assert len(cache) == 2
    assert "a" in cache and "b" in cache


def test_clear_drops_all_entries_and_resets_bytes():
    cache: LRUCache[bytes] = LRUCache(max_items=100, max_bytes=8)
    cache["a"] = b"aaaa"
    cache["b"] = b"bbbb"
    cache.clear()
    assert len(cache) == 0
    assert "a" not in cache
    # byte total reset, so the bound is fully available again
    cache["c"] = b"cccccccc"
    assert "c" in cache


# ── json_url_for ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url,expected",
    [
        pytest.param(
            "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/doc.pdf?download=true",
            "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/doc.json?download=true",
            id="standard-hf-pdf",
        ),
        pytest.param(
            "https://example.com/doc.pdf",
            None,
            id="non-huggingface",
        ),
        pytest.param(
            "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/doc.txt",
            None,
            id="huggingface-non-pdf",
        ),
        pytest.param(
            "https://huggingface.co/buckets/file.pdf.extra.pdf",
            "https://huggingface.co/buckets/file.json.extra.pdf",
            id="replaces-first-pdf-only",
        ),
    ],
)
def test_json_url_for(url, expected):
    assert json_url_for(url) == expected


# ── read_pdf_range with cached data ─────────────────────────────────


async def test_read_pdf_range_from_cache():
    url = "https://example.com/cached.pdf"
    data = b"0123456789" * 100
    pdf_cache[url] = data

    chunk, total = await read_pdf_range(url, 0, 50)
    assert chunk == data[:50]
    assert total == len(data)


async def test_read_pdf_range_from_cache_offset():
    url = "https://example.com/cached.pdf"
    data = b"ABCDEFGHIJ"
    pdf_cache[url] = data

    chunk, total = await read_pdf_range(url, 3, 4)
    assert chunk == b"DEFG"
    assert total == 10


async def test_read_pdf_range_from_cache_beyond_end():
    url = "https://example.com/cached.pdf"
    data = b"short"
    pdf_cache[url] = data

    chunk, total = await read_pdf_range(url, 3, 100)
    assert chunk == b"rt"
    assert total == 5


# ── read_pdf_range with HTTP Range (206) ─────────────────────────────


async def test_read_pdf_range_http_206():
    url = "https://example.com/remote.pdf"
    mock_response = MagicMock()
    mock_response.status_code = 206
    mock_response.content = b"partial-data"
    mock_response.headers = {"Content-Range": "bytes 0-11/1000"}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("ra_mcp_pdf_mcp.cache.httpx.AsyncClient", return_value=mock_client):
        chunk, total = await read_pdf_range(url, 0, 12)

    assert chunk == b"partial-data"
    assert total == 1000


async def test_read_pdf_range_http_206_unknown_size():
    url = "https://example.com/remote.pdf"
    mock_response = MagicMock()
    mock_response.status_code = 206
    mock_response.content = b"data"
    mock_response.headers = {"Content-Range": "bytes 0-3/*"}

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("ra_mcp_pdf_mcp.cache.httpx.AsyncClient", return_value=mock_client):
        chunk, total = await read_pdf_range(url, 0, 4)

    assert chunk == b"data"
    assert total == 0


# ── read_pdf_range with full GET (200) ───────────────────────────────


async def test_read_pdf_range_http_200_caches():
    url = "https://example.com/full.pdf"
    full_data = b"A" * 500

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = full_data
    mock_response.headers = {"Content-Length": str(len(full_data))}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("ra_mcp_pdf_mcp.cache.httpx.AsyncClient", return_value=mock_client):
        chunk, total = await read_pdf_range(url, 10, 50)

    assert chunk == full_data[10:60]
    assert total == 500
    assert pdf_cache[url] == full_data


async def test_read_pdf_range_too_large_raises():
    url = "https://example.com/huge.pdf"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"x"
    mock_response.headers = {"Content-Length": str(MAX_PDF_SIZE + 1)}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("ra_mcp_pdf_mcp.cache.httpx.AsyncClient", return_value=mock_client), pytest.raises(ValueError, match="too large"):
        await read_pdf_range(url, 0, 100)


# ── read_pdf_range with 501 fallback ─────────────────────────────────


async def test_read_pdf_range_501_falls_back_to_full_get():
    url = "https://example.com/no-range.pdf"
    full_data = b"full-content-here"

    resp_501 = MagicMock()
    resp_501.status_code = 501

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.content = full_data
    resp_200.headers = {"Content-Length": str(len(full_data))}
    resp_200.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[resp_501, resp_200])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("ra_mcp_pdf_mcp.cache.httpx.AsyncClient", return_value=mock_client):
        chunk, total = await read_pdf_range(url, 0, 5)

    assert chunk == b"full-"
    assert total == len(full_data)

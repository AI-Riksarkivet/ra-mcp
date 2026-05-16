"""Tests for ra_mcp_pdf_mcp.cache."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ra_mcp_pdf_mcp.cache import (
    MAX_PDF_SIZE,
    json_url_for,
    pdf_cache,
    read_pdf_range,
)


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

    with patch("ra_mcp_pdf_mcp.cache.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ValueError, match="too large"):
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

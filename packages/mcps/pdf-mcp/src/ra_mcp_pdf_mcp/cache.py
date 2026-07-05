"""PDF and structured JSON caching, prefetching, and byte-range reading."""

from __future__ import annotations

import asyncio
import logging
from collections import OrderedDict
from urllib.parse import urlparse

import httpx
from opentelemetry import trace
from opentelemetry.trace import SpanKind


logger = logging.getLogger("ra_mcp.pdf.cache")
_tracer = trace.get_tracer("ra_mcp.pdf.cache")


def _host(url: str) -> str:
    return urlparse(url).hostname or ""


MAX_PDF_SIZE = 200 * 1024 * 1024  # 200 MB — largest single PDF we'll cache
MAX_PDF_CACHE_BYTES = 512 * 1024 * 1024  # 512 MB total across all cached PDF bytes
MAX_PDF_CACHE_ITEMS = 16
MAX_BLOCKS_CACHE_ITEMS = 64
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB


def _sizeof(value: object) -> int:
    """Byte weight of a cached value — 0 for non-bytes, so those bound by count only."""
    return len(value) if isinstance(value, bytes | bytearray) else 0


class LRUCache[V]:
    """Least-recently-used cache bounded by item count and optional total bytes.

    Supports the dict-style operations the PDF caches use (``k in cache``,
    ``cache[k]``, ``cache[k] = v``, ``len(cache)``, truthiness) and evicts the
    least-recently-used entries once a bound is exceeded — so a long-running
    server can't accumulate PDF bytes without limit (the previous plain dicts
    grew forever, each entry up to MAX_PDF_SIZE).
    """

    def __init__(self, *, max_items: int, max_bytes: int | None = None) -> None:
        self._max_items = max_items
        self._max_bytes = max_bytes
        self._store: OrderedDict[str, V] = OrderedDict()
        self._bytes = 0

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __getitem__(self, key: str) -> V:
        self._store.move_to_end(key)
        return self._store[key]

    def __setitem__(self, key: str, value: V) -> None:
        if key in self._store:
            self._bytes -= _sizeof(self._store[key])
            del self._store[key]
        self._store[key] = value
        self._bytes += _sizeof(value)
        while self._store and (len(self._store) > self._max_items or (self._max_bytes is not None and self._bytes > self._max_bytes)):
            _, evicted = self._store.popitem(last=False)
            self._bytes -= _sizeof(evicted)

    def __len__(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        """Drop all entries and reset the byte total."""
        self._store.clear()
        self._bytes = 0

    def keys(self) -> list[str]:
        """Snapshot of the cached keys (does not affect LRU recency)."""
        return list(self._store)

    def items(self) -> list[tuple[str, V]]:
        """Snapshot of the cached (key, value) pairs (does not affect LRU recency)."""
        return list(self._store.items())


pdf_cache: LRUCache[bytes] = LRUCache(max_items=MAX_PDF_CACHE_ITEMS, max_bytes=MAX_PDF_CACHE_BYTES)
blocks_cache: LRUCache[list] = LRUCache(max_items=MAX_BLOCKS_CACHE_ITEMS)  # url → page dicts with structured blocks

_background_tasks: set[asyncio.Task] = set()


def json_url_for(pdf_url: str) -> str | None:
    """Derive structured JSON URL from a PDF URL (.pdf → .json)."""
    if "huggingface.co" not in pdf_url or ".pdf" not in pdf_url:
        return None
    return pdf_url.replace(".pdf", ".json", 1)


async def preload_all_guides() -> None:
    """Pre-load structured JSONs for all gallery PDFs at server startup."""
    from ra_mcp_pdf_mcp.gallery import GALLERY_ITEMS

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, read=60.0), follow_redirects=True) as client:
        for item in GALLERY_ITEMS:
            url = item["url"]
            j_url = json_url_for(url)
            if not j_url or url in blocks_cache:
                continue
            try:
                resp = await client.get(j_url)
                if resp.status_code == 200:
                    data = resp.json()
                    blocks_cache[url] = data.get("children", [])
                    logger.info("preloaded JSON (%d pages) for %s", len(blocks_cache[url]), item["title"])
            except Exception as e:
                logger.warning("failed to preload JSON for %s: %s", item["title"], e)


def schedule_prefetch(url: str) -> None:
    """Background prefetch of PDF bytes + structured JSON."""
    task = asyncio.create_task(_prefetch(url))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _prefetch(url: str) -> None:
    # Detached background task (fired from display_pdf), so it lives outside the
    # tool's SERVER span — give it its own span so failures aren't log-only.
    with _tracer.start_as_current_span("prefetch pdf", attributes={"server.address": _host(url)}):
        await _prefetch_inner(url)


async def _prefetch_inner(url: str) -> None:
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=120.0), follow_redirects=True) as client:
        if url not in pdf_cache:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                if len(resp.content) <= MAX_PDF_SIZE:
                    pdf_cache[url] = resp.content
                    logger.info("pre-cached %d bytes for %s", len(resp.content), url)
            except Exception as e:
                logger.warning("PDF pre-fetch failed for %s: %s", url, e)

        j_url = json_url_for(url)
        if j_url and url not in blocks_cache:
            try:
                resp = await client.get(j_url)
                if resp.status_code == 200:
                    data = resp.json()
                    blocks_cache[url] = data.get("children", [])
                    logger.info("cached structured JSON (%d pages) for %s", len(blocks_cache[url]), url)
            except Exception as e:
                logger.debug("no structured JSON for %s: %s", url, e)


async def read_pdf_range(url: str, offset: int, length: int) -> tuple[bytes, int]:
    """Read a byte range from a PDF. Returns (chunk_bytes, total_size).

    Uses HTTP Range requests when supported, falls back to full GET + cache.
    """
    if url in pdf_cache:
        data = pdf_cache[url]
        return data[offset : offset + length], len(data)

    with _tracer.start_as_current_span(
        "fetch pdf range",
        kind=SpanKind.CLIENT,
        attributes={"server.address": _host(url), "url.full": url, "http.request.method": "GET"},
    ):
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=120.0), follow_redirects=True) as client:
            end_byte = offset + length - 1
            resp = await client.get(url, headers={"Range": f"bytes={offset}-{end_byte}"})

            if resp.status_code == 206:
                content_range = resp.headers.get("Content-Range", "")
                total = 0
                if "/" in content_range:
                    size_str = content_range.rsplit("/", 1)[-1]
                    if size_str != "*":
                        total = int(size_str)
                return resp.content, total

            if resp.status_code == 501:
                resp = await client.get(url)
                resp.raise_for_status()

            if resp.status_code == 200:
                data = resp.content
                content_length = int(resp.headers.get("Content-Length", len(data)))
                if content_length > MAX_PDF_SIZE:
                    msg = f"PDF too large to cache: {content_length} bytes (max {MAX_PDF_SIZE})"
                    raise ValueError(msg)
                pdf_cache[url] = data
                return data[offset : offset + length], len(data)

            resp.raise_for_status()
            return b"", 0  # unreachable

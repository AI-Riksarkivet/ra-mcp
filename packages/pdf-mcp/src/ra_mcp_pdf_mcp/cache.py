"""PDF and structured JSON caching, prefetching, and byte-range reading."""

from __future__ import annotations

import asyncio
import logging

import httpx


logger = logging.getLogger("ra_mcp.pdf.cache")

MAX_PDF_SIZE = 200 * 1024 * 1024  # 200 MB
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB

pdf_cache: dict[str, bytes] = {}
blocks_cache: dict[str, list] = {}  # url → list of page dicts with structured blocks

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

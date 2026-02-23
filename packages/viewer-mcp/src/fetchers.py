"""
Async HTTP fetchers for document images, thumbnails, and text layer XML.

Uses httpx.AsyncClient with HTTP/2 and connection pooling, and
py-key-value-aio MemoryStore for TTL-based caching (replacing lru_cache).
CPU-bound Pillow work is offloaded via asyncio.to_thread.
"""

import asyncio
import base64
import io
import logging

import httpx
from fastmcp.telemetry import get_tracer
from key_value.aio.stores.memory import MemoryStore
from PIL import Image

from src.parser import detect_and_parse

logger = logging.getLogger(__name__)
tracer = get_tracer()

_EMPTY_TEXT_LAYER: dict = {"textLines": [], "pageWidth": 0, "pageHeight": 0}

_http = httpx.AsyncClient(
    http2=True,
    transport=httpx.AsyncHTTPTransport(retries=1),
    timeout=httpx.Timeout(connect=10, read=60, write=10, pool=5),
    follow_redirects=True,
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
)

_cache = MemoryStore(max_entries_per_collection=128)

_COL_IMAGES = "images"
_COL_THUMBNAILS = "thumbnails"
_COL_TEXT_LAYERS = "text_layers"

_TTL_IMAGES = 300
_TTL_THUMBNAILS = 600
_TTL_TEXT_LAYERS = 300

# Inflight dedup — prevents duplicate HTTP requests for the same URL
_inflight: dict[str, asyncio.Task] = {}


async def _dedup(key: str, coro):  # noqa: ANN001
    """If a fetch for `key` is already in flight, await it instead of starting a new one."""
    if key in _inflight:
        return await _inflight[key]
    task = asyncio.ensure_future(coro)
    _inflight[key] = task
    try:
        return await task
    finally:
        _inflight.pop(key, None)


async def _cache_get(key: str, collection: str) -> dict | None:
    """Get from cache, returning None on cache miss or missing collection."""
    try:
        return await _cache.get(key=key, collection=collection)
    except KeyError:
        return None


async def fetch_xml_from_url(url: str) -> str:
    """Fetch XML (ALTO/PAGE) from a URL and return raw text."""
    logger.debug("Fetching XML: %s", url)
    response = await _http.get(url, timeout=30.0)
    response.raise_for_status()
    logger.debug("XML fetched: status=%d, length=%d", response.status_code, len(response.text))
    return response.text


async def fetch_image_as_data_url(url: str) -> str:
    """Fetch image and return as base64 data URL. Cached + deduped by URL."""
    async def _fetch():
        cached = await _cache_get(url, _COL_IMAGES)
        if cached is not None:
            return cached["data_url"]
        with tracer.start_as_current_span("fetch_image", attributes={"url": url}):
            logger.debug("Fetching image: %s", url)
            resp = await _http.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg")
            b64 = base64.b64encode(resp.content).decode("ascii")
            logger.info("Image fetched: %d bytes (%s)", len(resp.content), content_type)
            data_url = f"data:{content_type};base64,{b64}"
        await _cache.put(key=url, value={"data_url": data_url}, collection=_COL_IMAGES, ttl=_TTL_IMAGES)
        return data_url
    return await _dedup(f"img:{url}", _fetch())


def _resize_thumbnail(raw: bytes, max_width: int) -> tuple[str, int, int]:
    """CPU-bound thumbnail resize — called via asyncio.to_thread."""
    img = Image.open(io.BytesIO(raw))
    ratio = max_width / img.width
    new_height = int(img.height * ratio)
    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}", max_width, new_height


async def fetch_thumbnail_as_data_url(url: str, max_width: int = 150) -> str:
    """Fetch image, resize to thumbnail, return as base64 data URL. Cached + deduped by URL."""
    async def _fetch():
        cached = await _cache_get(url, _COL_THUMBNAILS)
        if cached is not None:
            return cached["data_url"]
        with tracer.start_as_current_span("fetch_thumbnail", attributes={"url": url, "max_width": max_width}):
            logger.debug("Fetching thumbnail: %s", url)
            resp = await _http.get(url)
            resp.raise_for_status()
            data_url, w, h = await asyncio.to_thread(_resize_thumbnail, resp.content, max_width)
            logger.info("Thumbnail: %dx%d", w, h)
        await _cache.put(key=url, value={"data_url": data_url}, collection=_COL_THUMBNAILS, ttl=_TTL_THUMBNAILS)
        return data_url
    return await _dedup(f"thumb:{url}", _fetch())


async def fetch_and_parse_text_layer(url: str) -> dict:
    """Fetch ALTO/PAGE XML and parse into a text layer dict. Cached + deduped by URL."""
    async def _fetch():
        cached = await _cache_get(url, _COL_TEXT_LAYERS)
        if cached is not None:
            return cached
        with tracer.start_as_current_span("fetch_text_layer", attributes={"url": url}):
            xml = await fetch_xml_from_url(url)
            data = detect_and_parse(xml)
            result = {
                "textLines": [line.model_dump() for line in data.text_lines],
                "pageWidth": data.page_width,
                "pageHeight": data.page_height,
            }
        await _cache.put(key=url, value=result, collection=_COL_TEXT_LAYERS, ttl=_TTL_TEXT_LAYERS)
        return result
    return await _dedup(f"text:{url}", _fetch())


async def build_page_data(index: int, image_url: str, text_layer_url: str) -> tuple[dict, list[str]]:
    """Fetch image + text layer for a single page. Returns (page_dict, errors)."""
    page: dict = {"index": index}
    errors: list[str] = []

    try:
        page["imageDataUrl"] = await fetch_image_as_data_url(image_url)
    except Exception as e:
        logger.error("Image fetch failed for page %d: %s", index, e)
        errors.append(f"Page {index + 1} image: {e}")
        page["imageDataUrl"] = ""

    if text_layer_url:
        try:
            page["textLayer"] = await fetch_and_parse_text_layer(text_layer_url)
        except Exception as e:
            logger.error("Text layer fetch failed for page %d: %s", index, e)
            page["textLayer"] = _EMPTY_TEXT_LAYER
    else:
        page["textLayer"] = _EMPTY_TEXT_LAYER

    return page, errors

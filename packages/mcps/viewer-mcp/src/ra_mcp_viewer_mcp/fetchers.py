"""
Async HTTP fetchers for document text-layer XML.

Uses httpx.AsyncClient with HTTP/2 and connection pooling, and
py-key-value-aio MemoryStore for TTL-based caching of parsed text layers.
Page and thumbnail images are delivered as size-bounded IIIF URLs rendered
directly by the browser (see ``iiif_resize``) — no server-side image download,
resize, or base64 through the tool-result channel.
"""

import asyncio
import logging
from collections.abc import Coroutine

import httpx
from fastmcp.telemetry import get_tracer
from key_value.aio.stores.memory import MemoryStore

from ra_mcp_browse_lib.url_generator import iiif_resize
from ra_mcp_xml.parser import detect_and_parse


logger = logging.getLogger("ra_mcp.viewer.fetchers")
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

_COL_TEXT_LAYERS = "text_layers"
_TTL_TEXT_LAYERS = 300

# Inflight dedup — prevents duplicate HTTP requests for the same URL
_inflight: dict[str, asyncio.Task] = {}


async def _dedup[T](key: str, coro: Coroutine[object, object, T]) -> T:
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


async def fetch_and_parse_text_layer(url: str) -> dict:
    """Fetch ALTO/PAGE XML and parse into a text layer dict. Cached + deduped by URL."""

    async def _fetch() -> dict:
        cached = await _cache_get(url, _COL_TEXT_LAYERS)
        if cached is not None:
            return cached
        with tracer.start_as_current_span("fetch_text_layer", attributes={"url.full": url}):
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
    """Build the page payload: parse the text layer and hand back a size-bounded
    IIIF image URL for the browser to fetch directly.

    The image is NOT downloaded or base64-encoded server-side — ``imageDataUrl``
    carries a ``/full/1500,/`` IIIF URL (declared in the app's ResourceCSP
    ``resource_domains``). Returns (page_dict, errors).
    """
    errors: list[str] = []

    text_layer = _EMPTY_TEXT_LAYER
    if text_layer_url:
        try:
            text_layer = await fetch_and_parse_text_layer(text_layer_url)
        except Exception as e:
            logger.error("Text layer fetch failed for page %d: %s", index, e)

    return {"index": index, "imageDataUrl": iiif_resize(image_url, "1500,"), "textLayer": text_layer}, errors

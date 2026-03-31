"""PDF proxy handler — serves PDFs from upstream URLs with Range support.

Used by both standalone and composed servers to bypass iframe CSP restrictions.
PDF.js can load from this proxy using HTTP Range requests, fetching only the
pages the user actually views instead of the entire file.
"""

from __future__ import annotations

import logging

import httpx
from starlette.requests import Request
from starlette.responses import Response

from ra_mcp_pdf_mcp.state import get_proxy_url


logger = logging.getLogger("ra_mcp.pdf.proxy")


async def pdf_proxy_handler(request: Request) -> Response:
    """Proxy PDF requests. Forwards Range headers to the origin server."""
    view_id = request.path_params.get("view_id", "")
    url = get_proxy_url(view_id)
    if not url:
        return Response("Not found", status_code=404)

    # Forward Range header if present (for PDF.js incremental loading)
    headers: dict[str, str] = {}
    range_header = request.headers.get("range")
    if range_header:
        headers["Range"] = range_header

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, read=120.0),
            follow_redirects=True,
        ) as client:
            resp = await client.get(url, headers=headers)

        response_headers: dict[str, str] = {
            "Content-Type": resp.headers.get("Content-Type", "application/pdf"),
            "Access-Control-Allow-Origin": "*",
            "Accept-Ranges": "bytes",
        }

        if resp.headers.get("Content-Range"):
            response_headers["Content-Range"] = resp.headers["Content-Range"]
        if resp.headers.get("Content-Length"):
            response_headers["Content-Length"] = resp.headers["Content-Length"]

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=response_headers,
        )
    except Exception:
        logger.exception("PDF proxy error for view_id=%s", view_id)
        return Response("Proxy error", status_code=502)

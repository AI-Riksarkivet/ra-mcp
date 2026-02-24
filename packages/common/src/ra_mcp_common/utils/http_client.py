"""
HTTP client utility using httpx for all API requests.
Centralizes HTTP boilerplate code to avoid duplication.

Environment variables for debugging:
- RA_MCP_LOG_API: Enable API logging to file (ra_mcp_api.log)
- RA_MCP_LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR)
- RA_MCP_TIMEOUT: Override default timeout in seconds
"""

import asyncio
import contextlib
import json
import logging
import os
import time

import httpx
from opentelemetry.trace import SpanKind, StatusCode

from ra_mcp_common.telemetry import get_meter, get_tracer


logger = logging.getLogger("ra_mcp.http_client")


_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 0.5


class HTTPClient:
    """Centralized async HTTP client using httpx with comprehensive logging and retry."""

    def __init__(
        self,
        user_agent: str | None = None,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        backoff_base: float = _DEFAULT_BACKOFF_BASE,
        *,
        http2: bool = False,
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
        write_timeout: float = 10.0,
        pool_timeout: float = 5.0,
    ):
        if user_agent is None:
            from importlib.metadata import version

            user_agent = f"ra-mcp/{version('ra-mcp-common')}"
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.backoff_base = backoff_base

        self._client = httpx.AsyncClient(
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(connect=connect_timeout, read=read_timeout, write=write_timeout, pool=pool_timeout),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            follow_redirects=True,
            http2=http2,
        )

        # Telemetry
        self._tracer = get_tracer("ra_mcp.http_client")
        meter = get_meter("ra_mcp.http_client")
        self._request_counter = meter.create_counter("ra_mcp.http.requests", description="HTTP requests made")
        self._error_counter = meter.create_counter("ra_mcp.http.errors", description="HTTP request errors")
        self._duration_histogram = meter.create_histogram("ra_mcp.http.request.duration", unit="s", description="HTTP request duration")
        self._response_size_histogram = meter.create_histogram("ra_mcp.http.response.size", unit="By", description="HTTP response body size")
        self._retry_counter = meter.create_counter("ra_mcp.http.retries", description="HTTP request retry attempts")

    async def _execute_with_retry(
        self, method: str, url: str, *, params: dict | None = None, headers: dict[str, str] | None = None, timeout: float
    ) -> httpx.Response:
        """Execute a request with exponential backoff retry on transient errors.

        Returns the response object.
        Raises on non-retryable errors or after all retries exhausted.
        """
        last_exception: Exception = Exception("All retries exhausted")
        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(method, url, params=params, headers=headers, timeout=timeout)
                if response.status_code in _RETRYABLE_STATUS_CODES:
                    wait = self.backoff_base * (2**attempt)
                    logger.warning("Retryable status %d from %s, attempt %d/%d, waiting %.1fs", response.status_code, url, attempt + 1, self.max_retries, wait)
                    self._retry_counter.add(1, {"retry.reason": str(response.status_code)})
                    await asyncio.sleep(wait)
                    last_exception = Exception(f"HTTP {response.status_code}")
                    continue
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code in _RETRYABLE_STATUS_CODES:
                    wait = self.backoff_base * (2**attempt)
                    logger.warning("Retryable HTTP %d from %s, attempt %d/%d, waiting %.1fs", e.response.status_code, url, attempt + 1, self.max_retries, wait)
                    self._retry_counter.add(1, {"retry.reason": str(e.response.status_code)})
                    await asyncio.sleep(wait)
                    last_exception = e
                    continue
                raise
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                reason = "TimeoutError" if isinstance(e, httpx.TimeoutException) else type(e).__name__
                wait = self.backoff_base * (2**attempt)
                logger.warning("Retryable %s from %s, attempt %d/%d, waiting %.1fs", reason, url, attempt + 1, self.max_retries, wait)
                self._retry_counter.add(1, {"retry.reason": reason})
                await asyncio.sleep(wait)
                last_exception = e
                continue
        raise last_exception

    async def get_json(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
        timeout: int = 30,
        headers: dict[str, str] | None = None,
    ) -> dict:
        """
        Make a GET request and return JSON response.

        Args:
            url: Base URL
            params: Query parameters
            timeout: Request timeout in seconds (can be overridden by RA_MCP_TIMEOUT env var)
            headers: Additional headers

        Returns:
            Parsed JSON response

        Raises:
            TimeoutError: On request timeout
            httpx.HTTPStatusError: On non-success HTTP status code
            httpx.ConnectError: On network connection error
            json.JSONDecodeError: On invalid JSON response
        """
        # Allow timeout override from environment (useful for Hugging Face)
        timeout = int(os.getenv("RA_MCP_TIMEOUT", timeout))

        # Log request details
        logger.info("GET JSON: %s", url)
        logger.debug("Timeout: %ds, Params: %s", timeout, params)

        request_headers = {"Accept": "application/json"}
        if headers:
            request_headers.update(headers)
            logger.debug("Headers: %s", headers)

        span_attrs = {"http.request.method": "GET", "url.full": url}

        with self._tracer.start_as_current_span("HTTP GET", kind=SpanKind.CLIENT, attributes=span_attrs) as span:
            start_time = time.perf_counter()

            try:
                logger.debug("Opening connection to %s...", url)
                response = await self._execute_with_retry("GET", url, params=params, headers=request_headers, timeout=float(timeout))
                logger.debug("Connection established, status: %d", response.status_code)

                if response.status_code != 200:
                    logger.error("Unexpected status code: %d", response.status_code)
                    raise Exception(f"HTTP {response.status_code}")

                logger.debug("Reading response content...")
                content = response.content
                content_size = len(content)
                logger.debug("Received %d bytes", content_size)

                logger.debug("Parsing JSON...")
                result = json.loads(content)

                duration = time.perf_counter() - start_time
                logger.info("✓ GET JSON %s - %.3fs - %d bytes - 200 OK", url, duration, content_size)

                span.set_attribute("http.response.status_code", response.status_code)
                span.set_attribute("http.response.body.size", content_size)
                self._response_size_histogram.record(content_size, {"http.request.method": "GET"})

                return result

            except httpx.TimeoutException as e:
                duration = time.perf_counter() - start_time
                logger.error("✗ TIMEOUT after %.3fs on %s", duration, url)
                logger.error("Timeout limit was %ds", timeout)
                span.set_status(StatusCode.ERROR, f"Timeout after {timeout}s")
                span.record_exception(e)
                self._error_counter.add(1, {"error.type": "TimeoutError"})
                raise TimeoutError(f"Request timeout after {timeout}s: {url}") from e

            except httpx.HTTPStatusError as e:
                duration = time.perf_counter() - start_time
                error_body = ""
                try:
                    error_body = e.response.text[:500]
                    logger.error("Error response body: %s", error_body)
                except Exception:
                    pass

                logger.error("✗ GET JSON %s - %.3fs - HTTPStatusError: %s", url, duration, e.response.status_code)

                span.set_status(StatusCode.ERROR, f"HTTPStatusError: {e.response.status_code}")
                span.record_exception(e)
                span.set_attribute("http.response.status_code", e.response.status_code)
                self._error_counter.add(1, {"error.type": "HTTPStatusError"})
                raise

            except (httpx.ConnectError, json.JSONDecodeError) as e:
                duration = time.perf_counter() - start_time
                error_type = type(e).__name__
                logger.error("✗ GET JSON %s - %.3fs - %s: %s", url, duration, error_type, e)

                span.set_status(StatusCode.ERROR, f"{error_type}: {e}")
                span.record_exception(e)
                self._error_counter.add(1, {"error.type": error_type})
                raise

            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error("✗ Unexpected error after %.3fs: %s: %s", duration, type(e).__name__, e)
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                self._error_counter.add(1, {"error.type": type(e).__name__})
                raise

            finally:
                self._request_counter.add(1, {"http.request.method": "GET"})
                self._duration_histogram.record(time.perf_counter() - start_time, {"http.request.method": "GET"})

    async def get_xml(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
        timeout: int = 30,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        """
        Make a GET request and return XML response as bytes.

        Args:
            url: Base URL
            params: Query parameters
            timeout: Request timeout in seconds
            headers: Additional headers

        Returns:
            XML response as bytes

        Raises:
            TimeoutError: On request timeout
            httpx.HTTPStatusError: On non-success HTTP status code
            httpx.ConnectError: On network connection error
        """
        logger.debug("GET XML: %s", url)

        request_headers = {"Accept": "application/xml, text/xml, */*"}
        if headers:
            request_headers.update(headers)

        span_attrs = {"http.request.method": "GET", "url.full": url}

        with self._tracer.start_as_current_span("HTTP GET", kind=SpanKind.CLIENT, attributes=span_attrs) as span:
            start_time = time.perf_counter()

            try:
                response = await self._execute_with_retry("GET", url, params=params, headers=request_headers, timeout=float(timeout))
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")

                content = response.content
                content_size = len(content)
                duration = time.perf_counter() - start_time
                logger.info("GET XML %s - %.3fs - 200 OK", url, duration)

                span.set_attribute("http.response.status_code", response.status_code)
                span.set_attribute("http.response.body.size", content_size)
                self._response_size_histogram.record(content_size, {"http.request.method": "GET"})

                return content

            except httpx.TimeoutException as e:
                duration = time.perf_counter() - start_time
                logger.error("GET XML %s - %.3fs - ERROR: TimeoutError", url, duration)
                span.set_status(StatusCode.ERROR, f"TimeoutError: {e}")
                span.record_exception(e)
                self._error_counter.add(1, {"error.type": "TimeoutError"})
                raise TimeoutError(f"Request timeout: {url}") from e

            except httpx.HTTPStatusError as e:
                duration = time.perf_counter() - start_time
                error_body = ""
                with contextlib.suppress(Exception):
                    error_body = f" - Body: {e.response.text[:500]}"
                logger.error("GET XML %s - %.3fs - ERROR: %s%s", url, duration, e.response.status_code, error_body)

                span.set_status(StatusCode.ERROR, f"HTTPStatusError: {e.response.status_code}")
                span.record_exception(e)
                span.set_attribute("http.response.status_code", e.response.status_code)
                self._error_counter.add(1, {"error.type": "HTTPStatusError"})
                raise

            except httpx.ConnectError as e:
                duration = time.perf_counter() - start_time
                logger.error("GET XML %s - %.3fs - ERROR: %s", url, duration, e)
                span.set_status(StatusCode.ERROR, f"ConnectError: {e}")
                span.record_exception(e)
                self._error_counter.add(1, {"error.type": "ConnectError"})
                raise

            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error("GET XML %s - %.3fs - ERROR: %s", url, duration, e)
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                self._error_counter.add(1, {"error.type": type(e).__name__})
                raise

            finally:
                self._request_counter.add(1, {"http.request.method": "GET"})
                self._duration_histogram.record(time.perf_counter() - start_time, {"http.request.method": "GET"})

    async def get_content(self, url: str, timeout: int = 30, headers: dict[str, str] | None = None) -> bytes | None:
        """
        Make a GET request and return raw content.
        Returns None on 404 or errors.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            headers: Additional headers

        Returns:
            Response content as bytes or None
        """
        logger.debug("GET CONTENT: %s", url)

        request_headers: dict[str, str] = {}
        if headers:
            request_headers.update(headers)

        span_attrs = {"http.request.method": "GET", "url.full": url}

        with self._tracer.start_as_current_span("HTTP GET", kind=SpanKind.CLIENT, attributes=span_attrs) as span:
            start_time = time.perf_counter()

            try:
                response = await self._execute_with_retry("GET", url, headers=request_headers, timeout=float(timeout))
                duration = time.perf_counter() - start_time
                span.set_attribute("http.response.status_code", response.status_code)

                if response.status_code == 404:
                    logger.info("GET %s - %.3fs - 404 NOT FOUND", url, duration)
                    return None
                if response.status_code != 200:
                    logger.warning("GET %s - %.3fs - %d", url, duration, response.status_code)
                    return None

                content = response.content
                content_size = len(content)
                logger.info("GET %s - %.3fs - 200 OK", url, duration)

                span.set_attribute("http.response.body.size", content_size)
                self._response_size_histogram.record(content_size, {"http.request.method": "GET"})
                return content

            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
                duration = time.perf_counter() - start_time
                error_type = "TimeoutError" if isinstance(e, httpx.TimeoutException) else type(e).__name__
                error_msg = str(e.response.status_code) if isinstance(e, httpx.HTTPStatusError) else str(e)
                logger.error("GET %s - %.3fs - ERROR: %s", url, duration, error_msg)
                span.set_status(StatusCode.ERROR, f"{error_type}: {error_msg}")
                span.record_exception(e)
                self._error_counter.add(1, {"error.type": error_type})
                return None
            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error("GET %s - ERROR: %s", url, e)
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                self._error_counter.add(1, {"error.type": type(e).__name__})
                return None
            finally:
                self._request_counter.add(1, {"http.request.method": "GET"})
                self._duration_histogram.record(time.perf_counter() - start_time, {"http.request.method": "GET"})

    async def aclose(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()


default_http_client = HTTPClient()


def get_http_client(enable_logging: bool = False) -> HTTPClient:
    """Get the default shared HTTP client instance.

    Args:
        enable_logging: If True, attach a file handler to the root logger
            that writes to ``ra_mcp_api.log``.
    """
    if enable_logging:
        root = logging.getLogger()
        # Avoid adding duplicate file handlers
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith("ra_mcp_api.log") for h in root.handlers):
            fh = logging.FileHandler("ra_mcp_api.log")
            fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
            root.addHandler(fh)
    return default_http_client

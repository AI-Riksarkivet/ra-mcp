"""
HTTP client utility using urllib for all API requests.
Centralizes urllib boilerplate code to avoid duplication.

Environment variables for debugging:
- RA_MCP_LOG_API: Enable API logging to file (ra_mcp_api.log)
- RA_MCP_LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR)
- RA_MCP_TIMEOUT: Override default timeout in seconds
"""

import json
import logging
import os
import sys
import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from typing import Dict, Optional, Union

from opentelemetry.trace import SpanKind, StatusCode

from ra_mcp_common.telemetry import get_tracer, get_meter


logger = logging.getLogger(__name__)


_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 0.5


class HTTPClient:
    """Centralized HTTP client using urllib with comprehensive logging and retry."""

    def __init__(self, user_agent: str | None = None, max_retries: int = _DEFAULT_MAX_RETRIES, backoff_base: float = _DEFAULT_BACKOFF_BASE):
        if user_agent is None:
            from importlib.metadata import version

            user_agent = f"ra-mcp/{version('ra-mcp-common')}"
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.logger = logging.getLogger("ra_mcp.http_client")
        self.debug_console = os.getenv("RA_MCP_LOG_API")

        # Configure logging level from environment
        log_level = os.getenv("RA_MCP_LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Set up logging handlers
        self._setup_logging()

        # Telemetry
        self._tracer = get_tracer("ra_mcp.http_client")
        meter = get_meter("ra_mcp.http_client")
        self._request_counter = meter.create_counter("ra_mcp.http.requests", description="HTTP requests made")
        self._error_counter = meter.create_counter("ra_mcp.http.errors", description="HTTP request errors")
        self._duration_histogram = meter.create_histogram("ra_mcp.http.request.duration", unit="s", description="HTTP request duration")
        self._response_size_histogram = meter.create_histogram("ra_mcp.http.response.size", unit="By", description="HTTP response body size")
        self._retry_counter = meter.create_counter("ra_mcp.http.retries", description="HTTP request retry attempts")

        logger.info(f"HTTPClient initialized with user agent: {self.user_agent}")

    def _setup_logging(self):
        """Configure logging handlers for file and console output."""
        if not self.logger.handlers:
            # File handler for persistent logs
            if self.debug_console or os.getenv("RA_MCP_LOG_API"):
                file_handler = logging.FileHandler("ra_mcp_api.log")
                file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
                self.logger.addHandler(file_handler)

            # Console handler for stderr (visible in Hugging Face logs)
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(logging.Formatter("%(levelname)s - %(name)s - %(message)s"))
            self.logger.addHandler(console_handler)

    def _execute_with_retry(self, request, timeout, url):
        """Execute a request with exponential backoff retry on transient errors.

        Returns the response object (caller must read content within context).
        Raises on non-retryable errors or after all retries exhausted.
        """
        last_exception: Exception = Exception("All retries exhausted")
        for attempt in range(self.max_retries):
            try:
                response = urlopen(request, timeout=timeout)
                if response.status in _RETRYABLE_STATUS_CODES:
                    wait = self.backoff_base * (2**attempt)
                    self.logger.warning(f"Retryable status {response.status} from {url}, attempt {attempt + 1}/{self.max_retries}, waiting {wait:.1f}s")
                    response.close()
                    self._retry_counter.add(1, {"retry.reason": str(response.status)})
                    time.sleep(wait)
                    last_exception = Exception(f"HTTP {response.status}")
                    continue
                return response
            except HTTPError as e:
                if e.code in _RETRYABLE_STATUS_CODES:
                    wait = self.backoff_base * (2**attempt)
                    self.logger.warning(f"Retryable HTTP {e.code} from {url}, attempt {attempt + 1}/{self.max_retries}, waiting {wait:.1f}s")
                    self._retry_counter.add(1, {"retry.reason": str(e.code)})
                    time.sleep(wait)
                    last_exception = e
                    continue
                raise
            except (TimeoutError, URLError) as e:
                wait = self.backoff_base * (2**attempt)
                self.logger.warning(f"Retryable {type(e).__name__} from {url}, attempt {attempt + 1}/{self.max_retries}, waiting {wait:.1f}s")
                self._retry_counter.add(1, {"retry.reason": type(e).__name__})
                time.sleep(wait)
                last_exception = e
                continue
        raise last_exception

    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Union[str, int]]] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict:
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
            Exception: On HTTP errors or invalid JSON
        """
        # Allow timeout override from environment (useful for Hugging Face)
        timeout = int(os.getenv("RA_MCP_TIMEOUT", timeout))

        # Build URL with parameters
        if params:
            query_string = urlencode(params)
            full_url = f"{url}?{query_string}"
        else:
            full_url = url

        # Log request details
        self.logger.info(f"GET JSON: {full_url}")
        self.logger.debug(f"Timeout: {timeout}s, Params: {params}")

        # Create request with headers
        request = Request(full_url)
        request.add_header("User-Agent", self.user_agent)
        request.add_header("Accept", "application/json")

        if headers:
            for key, value in headers.items():
                request.add_header(key, value)
            self.logger.debug(f"Headers: {headers}")

        span_attrs = {"http.request.method": "GET", "url.full": full_url}

        with self._tracer.start_as_current_span("HTTP GET", kind=SpanKind.CLIENT, attributes=span_attrs) as span:
            start_time = time.perf_counter()

            try:
                self.logger.debug(f"Opening connection to {url}...")
                with self._execute_with_retry(request, timeout, url) as response:
                    self.logger.debug(f"Connection established, status: {response.status}")

                    if response.status != 200:
                        self.logger.error(f"Unexpected status code: {response.status}")
                        raise Exception(f"HTTP {response.status}")

                    self.logger.debug("Reading response content...")
                    content = response.read()
                    content_size = len(content)
                    self.logger.debug(f"Received {content_size} bytes")

                    self.logger.debug("Parsing JSON...")
                    result = json.loads(content)

                    duration = time.perf_counter() - start_time
                    self.logger.info(f"✓ GET JSON {full_url} - {duration:.3f}s - {content_size} bytes - 200 OK")

                    span.set_attribute("http.response.status_code", response.status)
                    span.set_attribute("http.response.body.size", content_size)
                    self._request_counter.add(1, {"http.request.method": "GET", "url.template": url})
                    self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                    self._response_size_histogram.record(content_size, {"http.request.method": "GET", "url.template": url})

                    return result

            except TimeoutError as e:
                duration = time.perf_counter() - start_time
                self.logger.error(f"✗ TIMEOUT after {duration:.3f}s on {full_url}")
                self.logger.error(f"Timeout limit was {timeout}s")
                span.set_status(StatusCode.ERROR, f"Timeout after {timeout}s")
                span.record_exception(e)
                self._error_counter.add(1, {"http.request.method": "GET", "url.template": url, "error.type": "TimeoutError"})
                self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                raise Exception(f"Request timeout after {timeout}s: {url}") from e

            except (HTTPError, URLError, json.JSONDecodeError) as e:
                duration = time.perf_counter() - start_time
                error_type = type(e).__name__
                error_msg = str(e.code) if hasattr(e, "code") else str(e)

                error_body = ""
                if isinstance(e, HTTPError):
                    try:
                        # Get first 500 chars of error body
                        error_body = e.read().decode("utf-8")[:500]
                        self.logger.error(f"Error response body: {error_body}")
                    except Exception:
                        pass

                self.logger.error(f"✗ GET JSON {full_url} - {duration:.3f}s - {error_type}: {error_msg}")

                span.set_status(StatusCode.ERROR, f"{error_type}: {error_msg}")
                span.record_exception(e)
                if isinstance(e, HTTPError):
                    span.set_attribute("http.response.status_code", e.code)
                self._error_counter.add(1, {"http.request.method": "GET", "url.template": url, "error.type": error_type})
                self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})

                if isinstance(e, HTTPError):
                    raise Exception(f"HTTP Error {e.code}: {e.reason}") from e
                elif isinstance(e, URLError):
                    raise Exception(f"URL Error: {e.reason}") from e
                else:
                    raise Exception(f"Invalid JSON response: {e}") from e

            except Exception as e:
                duration = time.perf_counter() - start_time
                self.logger.error(f"✗ Unexpected error after {duration:.3f}s: {type(e).__name__}: {e}")
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                self._error_counter.add(1, {"http.request.method": "GET", "url.template": url, "error.type": type(e).__name__})
                self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                raise

    def get_xml(
        self,
        url: str,
        params: Optional[Dict[str, Union[str, int]]] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
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
            Exception: On HTTP errors
        """
        # Build URL with parameters
        if params:
            query_string = urlencode(params)
            full_url = f"{url}?{query_string}"
        else:
            full_url = url

        # Debug: Print URL to console
        if self.debug_console:
            print(f"[DEBUG] GET XML: {full_url}", file=sys.stderr)

        # Create request with headers
        request = Request(full_url)
        request.add_header("User-Agent", self.user_agent)
        request.add_header("Accept", "application/xml, text/xml, */*")

        if headers:
            for key, value in headers.items():
                request.add_header(key, value)

        span_attrs = {"http.request.method": "GET", "url.full": full_url}

        with self._tracer.start_as_current_span("HTTP GET", kind=SpanKind.CLIENT, attributes=span_attrs) as span:
            start_time = time.perf_counter()

            try:
                with self._execute_with_retry(request, timeout, url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")

                    content = response.read()
                    content_size = len(content)
                    duration = time.perf_counter() - start_time
                    self.logger.info(f"GET XML {full_url} - {duration:.3f}s - 200 OK")

                    span.set_attribute("http.response.status_code", response.status)
                    span.set_attribute("http.response.body.size", content_size)
                    self._request_counter.add(1, {"http.request.method": "GET", "url.template": url})
                    self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                    self._response_size_histogram.record(content_size, {"http.request.method": "GET", "url.template": url})

                    return content

            except (HTTPError, URLError) as e:
                duration = time.perf_counter() - start_time
                error_type = type(e).__name__
                error_msg = str(e.code) if hasattr(e, "code") else str(e)
                error_body = ""
                if isinstance(e, HTTPError):
                    try:
                        error_body = e.read().decode("utf-8")[:500]
                        error_body = f" - Body: {error_body}"
                    except Exception:
                        pass
                self.logger.error(f"GET XML {full_url} - {duration:.3f}s - ERROR: {error_msg}{error_body}")

                span.set_status(StatusCode.ERROR, f"{error_type}: {error_msg}")
                span.record_exception(e)
                if isinstance(e, HTTPError):
                    span.set_attribute("http.response.status_code", e.code)
                self._error_counter.add(1, {"http.request.method": "GET", "url.template": url, "error.type": error_type})
                self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})

                if isinstance(e, HTTPError):
                    raise Exception(f"HTTP Error {e.code}: {e.reason}") from e
                else:
                    raise Exception(f"URL Error: {e.reason}") from e

    def get_content(self, url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> Optional[bytes]:
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
        # Debug: Print URL to console
        if self.debug_console:
            print(f"[DEBUG] GET CONTENT: {url}", file=sys.stderr)

        # Create request with headers
        request = Request(url)
        request.add_header("User-Agent", self.user_agent)

        if headers:
            for key, value in headers.items():
                request.add_header(key, value)

        span_attrs = {"http.request.method": "GET", "url.full": url}

        with self._tracer.start_as_current_span("HTTP GET", kind=SpanKind.CLIENT, attributes=span_attrs) as span:
            start_time = time.perf_counter()

            try:
                with self._execute_with_retry(request, timeout, url) as response:
                    duration = time.perf_counter() - start_time
                    span.set_attribute("http.response.status_code", response.status)

                    if response.status == 404:
                        self.logger.info(f"GET {url} - {duration:.3f}s - 404 NOT FOUND")
                        self._request_counter.add(1, {"http.request.method": "GET", "url.template": url})
                        self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                        return None
                    if response.status != 200:
                        self.logger.warning(f"GET {url} - {duration:.3f}s - {response.status}")
                        self._request_counter.add(1, {"http.request.method": "GET", "url.template": url})
                        self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                        return None

                    content = response.read()
                    content_size = len(content)
                    self.logger.info(f"GET {url} - {duration:.3f}s - 200 OK")

                    span.set_attribute("http.response.body.size", content_size)
                    self._request_counter.add(1, {"http.request.method": "GET", "url.template": url})
                    self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                    self._response_size_histogram.record(content_size, {"http.request.method": "GET", "url.template": url})
                    return content

            except (HTTPError, URLError, TimeoutError) as e:
                duration = time.perf_counter() - start_time
                error_type = type(e).__name__
                error_msg = str(e.code) if hasattr(e, "code") else str(e)
                self.logger.error(f"GET {url} - {duration:.3f}s - ERROR: {error_msg}")
                span.set_status(StatusCode.ERROR, f"{error_type}: {error_msg}")
                span.record_exception(e)
                self._error_counter.add(1, {"http.request.method": "GET", "url.template": url, "error.type": error_type})
                self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                return None
            except Exception as e:
                duration = time.perf_counter() - start_time
                self.logger.error(f"GET {url} - ERROR: {str(e)}")
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                self._error_counter.add(1, {"http.request.method": "GET", "url.template": url, "error.type": type(e).__name__})
                self._duration_histogram.record(duration, {"http.request.method": "GET", "url.template": url})
                return None


default_http_client = HTTPClient()


def get_http_client(enable_logging: bool = False) -> HTTPClient:
    """Get HTTP client with optional logging enabled.

    Args:
        enable_logging: Whether to enable API call logging to ra_mcp_api.log

    Returns:
        HTTPClient instance with logging enabled or default client
    """
    import os

    if enable_logging:
        os.environ["RA_MCP_LOG_API"] = "1"
        return HTTPClient()
    return default_http_client

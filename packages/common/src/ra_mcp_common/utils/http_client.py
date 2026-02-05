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


logger = logging.getLogger(__name__)


class HTTPClient:
    """Centralized HTTP client using urllib with comprehensive logging."""

    def __init__(self, user_agent: str = "Transcribed-Search-Browser/1.0"):
        self.user_agent = user_agent
        self.logger = logging.getLogger("ra_mcp.http_client")
        self.debug_console = os.getenv("RA_MCP_LOG_API")

        # Configure logging level from environment
        log_level = os.getenv("RA_MCP_LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Set up logging handlers
        self._setup_logging()

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

        start_time = time.perf_counter()

        try:
            self.logger.debug(f"Opening connection to {url}...")
            with urlopen(request, timeout=timeout) as response:
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

                return result

        except TimeoutError as e:
            duration = time.perf_counter() - start_time
            self.logger.error(f"✗ TIMEOUT after {duration:.3f}s on {full_url}")
            self.logger.error(f"Timeout limit was {timeout}s")
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

            if isinstance(e, HTTPError):
                raise Exception(f"HTTP Error {e.code}: {e.reason}") from e
            elif isinstance(e, URLError):
                raise Exception(f"URL Error: {e.reason}") from e
            else:
                raise Exception(f"Invalid JSON response: {e}") from e

        except Exception as e:
            duration = time.perf_counter() - start_time
            self.logger.error(f"✗ Unexpected error after {duration:.3f}s: {type(e).__name__}: {e}")
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

        start_time = time.perf_counter() if self.logger else 0

        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                content = response.read()

                if self.logger and start_time:
                    duration = time.perf_counter() - start_time
                    self.logger.info(f"GET XML {full_url} - {duration:.3f}s - 200 OK")

                return content

        except (HTTPError, URLError) as e:
            if self.logger and start_time:
                duration = time.perf_counter() - start_time
                error_msg = str(e.code) if hasattr(e, "code") else str(e)
                error_body = ""
                if isinstance(e, HTTPError):
                    try:
                        # Get first 500 chars of error body
                        error_body = e.read().decode("utf-8")[:500]
                        error_body = f" - Body: {error_body}"
                    except Exception:
                        pass
                self.logger.error(f"GET XML {full_url} - {duration:.3f}s - ERROR: {error_msg}{error_body}")

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

        start_time = time.perf_counter() if self.logger else 0

        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status == 404:
                    if self.logger and start_time:
                        duration = time.perf_counter() - start_time
                        self.logger.info(f"GET {url} - {duration:.3f}s - 404 NOT FOUND")
                    return None
                if response.status != 200:
                    if self.logger and start_time:
                        duration = time.perf_counter() - start_time
                        self.logger.warning(f"GET {url} - {duration:.3f}s - {response.status}")
                    return None

                content = response.read()
                if self.logger and start_time:
                    duration = time.perf_counter() - start_time
                    self.logger.info(f"GET {url} - {duration:.3f}s - 200 OK")
                return content

        except (HTTPError, URLError, TimeoutError) as e:
            if self.logger and start_time:
                duration = time.perf_counter() - start_time
                error_msg = str(e.code) if hasattr(e, "code") else str(e)
                self.logger.error(f"GET {url} - {duration:.3f}s - ERROR: {error_msg}")
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"GET {url} - ERROR: {str(e)}")
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

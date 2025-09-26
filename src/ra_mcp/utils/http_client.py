"""
HTTP client utility using urllib for all API requests.
Centralizes urllib boilerplate code to avoid duplication.
"""

import json
import logging
import os
import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from typing import Dict, Optional, Union


class HTTPClient:
    """Centralized HTTP client using urllib."""

    def __init__(self, user_agent: str = "Transcribed-Search-Browser/1.0"):
        self.user_agent = user_agent
        self.logger = None

        if os.getenv("RA_MCP_LOG_API"):
            self.logger = logging.getLogger("ra_mcp.api")
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.FileHandler("ra_mcp_api.log")
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
                    )
                )
                self.logger.addHandler(handler)

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
            timeout: Request timeout in seconds
            headers: Additional headers

        Returns:
            Parsed JSON response

        Raises:
            Exception: On HTTP errors or invalid JSON
        """
        # Build URL with parameters
        if params:
            query_string = urlencode(params)
            full_url = f"{url}?{query_string}"
        else:
            full_url = url

        # Create request with headers
        request = Request(full_url)
        request.add_header("User-Agent", self.user_agent)
        request.add_header("Accept", "application/json")

        if headers:
            for key, value in headers.items():
                request.add_header(key, value)

        start_time = time.perf_counter() if self.logger else 0

        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                content = response.read()
                result = json.loads(content)

                if self.logger and start_time:
                    duration = time.perf_counter() - start_time
                    self.logger.info(f"GET JSON {full_url} - {duration:.3f}s - 200 OK")

                return result

        except (HTTPError, URLError, json.JSONDecodeError) as e:
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
                self.logger.error(
                    f"GET JSON {full_url} - {duration:.3f}s - "
                    f"ERROR: {error_msg}{error_body}"
                )

            if isinstance(e, HTTPError):
                raise Exception(f"HTTP Error {e.code}: {e.reason}") from e
            elif isinstance(e, URLError):
                raise Exception(f"URL Error: {e.reason}") from e
            else:
                raise Exception(f"Invalid JSON response: {e}") from e

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
                self.logger.error(
                    f"GET XML {full_url} - {duration:.3f}s - "
                    f"ERROR: {error_msg}{error_body}"
                )

            if isinstance(e, HTTPError):
                raise Exception(f"HTTP Error {e.code}: {e.reason}") from e
            else:
                raise Exception(f"URL Error: {e.reason}") from e

    def get_content(
        self, url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None
    ) -> Optional[bytes]:
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
                        self.logger.warning(
                            f"GET {url} - {duration:.3f}s - {response.status}"
                        )
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

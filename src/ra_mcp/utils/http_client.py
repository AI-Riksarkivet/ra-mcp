"""
HTTP client utility using urllib for all API requests.
Centralizes urllib boilerplate code to avoid duplication.
"""

import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from typing import Dict, Optional, Any


class HTTPClient:
    """Centralized HTTP client using urllib."""

    def __init__(self, user_agent: str = "Transcribed-Search-Browser/1.0"):
        self.user_agent = user_agent

    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
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

        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                content = response.read()
                return json.loads(content)

        except HTTPError as e:
            raise Exception(f"HTTP Error {e.code}: {e.reason}") from e
        except URLError as e:
            raise Exception(f"URL Error: {e.reason}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}") from e

    def get_xml(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
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

        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                return response.read()

        except HTTPError as e:
            raise Exception(f"HTTP Error {e.code}: {e.reason}") from e
        except URLError as e:
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

        try:
            with urlopen(request, timeout=timeout) as response:
                if response.status == 404:
                    return None
                if response.status != 200:
                    return None

                return response.read()

        except (HTTPError, URLError, TimeoutError):
            return None
        except Exception:
            return None


# Global instance for convenience
http_client = HTTPClient()

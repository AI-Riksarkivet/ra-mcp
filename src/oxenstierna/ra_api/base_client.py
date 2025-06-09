import httpx
from typing import Optional


class ApiClientError(Exception):
    """Base exception for API client errors."""

    pass


class RateLimitError(ApiClientError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class BaseRiksarkivetClient:
    """Base client for Riksarkivet APIs with common error handling and request functionality."""

    def _handle_riksarkivet_response(self, response: httpx.Response) -> None:
        """Handle common Riksarkivet API error responses."""
        if response.status_code == 400:
            raise ApiClientError("Bad Request - incorrect parameters")
        elif response.status_code == 403:
            raise ApiClientError(
                "Forbidden - the resource has no rights statement or is not available"
            )
        elif response.status_code == 404:
            raise ApiClientError("Not Found - missing resource")
        elif response.status_code == 429:
            retry_after = None
            for header_name, header_value in response.headers.items():
                if header_name.lower().startswith("x-ratelimit-reset"):
                    try:
                        retry_after = int(header_value)
                    except ValueError:
                        pass
            raise RateLimitError(
                "Too many requests - rate limit exceeded", retry_after=retry_after
            )
        elif response.status_code == 501:
            raise ApiClientError("Not Implemented - method not implemented")

        response.raise_for_status()

    async def _make_request(self, url: str) -> httpx.Response:
        """Make HTTP request with headers that work reliably with Riksarkivet."""
        headers = {
            "Connection": "close",
            "User-Agent": "curl/8.7.1",
            "Accept": "*/*",
        }

        async with httpx.AsyncClient(http2=False) as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)
                self._handle_riksarkivet_response(response)
                return response
            except (RateLimitError, ApiClientError):
                raise
            except httpx.HTTPStatusError as e:
                raise ApiClientError(f"HTTP error: {e}")
            except httpx.RequestError as e:
                raise ApiClientError(f"Request error: {e}")
            except Exception as e:
                raise ApiClientError(f"Unexpected error: {e}")

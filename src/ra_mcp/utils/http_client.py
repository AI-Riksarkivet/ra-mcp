"""
HTTP client utilities for Riksarkivet APIs.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class HTTPClient:
    """HTTP client with optimized settings for Riksarkivet APIs."""

    @staticmethod
    def create_session() -> requests.Session:
        """Create HTTP session optimized for Riksarkivet APIs."""
        session = requests.Session()
        session.headers.update({
            'Connection': 'close',
            'User-Agent': 'Transcribed-Search-Browser/1.0'
        })

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=1,
            pool_maxsize=1
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
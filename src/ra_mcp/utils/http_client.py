"""
HTTP client utilities for Riksarkivet APIs.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session() -> requests.Session:
    """Create HTTP session optimized for Riksarkivet APIs.

    Returns:
        Configured requests.Session with retry logic and connection pooling.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Transcribed-Search-Browser/1.0",
            "Accept-Encoding": "gzip, deflate",
        }
    )

    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10,
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

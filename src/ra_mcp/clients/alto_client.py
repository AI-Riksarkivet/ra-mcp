"""
ALTO XML client for Riksarkivet.
"""

import xml.etree.ElementTree as ET
from typing import Optional

from ..config import ALTO_NAMESPACES
from ..utils import HTTPClient


class ALTOClient:
    """Client for fetching and parsing ALTO XML files."""

    def __init__(self):
        self.session = HTTPClient.create_session()

    def fetch_content(self, alto_url: str, timeout: int = 10) -> Optional[str]:
        """Fetch and parse ALTO XML file to extract full text content."""
        try:
            headers = {
                "User-Agent": "transcribed_search_browser/1.0",
                "Accept": "application/xml, text/xml, */*",
            }

            response = self.session.get(alto_url, headers=headers, timeout=timeout)
            if response.status_code != 200:
                return None

            root = ET.fromstring(response.content)
            return self._extract_text_from_alto(root)

        except Exception:
            return None

    def _extract_text_from_alto(self, root: ET.Element) -> Optional[str]:
        """Extract text content from ALTO XML root element."""
        text_lines = []

        for ns in ALTO_NAMESPACES:
            for string_elem in root.findall(".//alto:String", ns):
                content = string_elem.get("CONTENT", "")
                if content:
                    text_lines.append(content)
            if text_lines:
                break

        if not text_lines:
            for string_elem in root.findall(".//String"):
                content = string_elem.get("CONTENT", "")
                if content:
                    text_lines.append(content)

        full_text = " ".join(text_lines)
        return full_text.strip() if full_text else None

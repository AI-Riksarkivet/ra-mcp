"""
ALTO XML client for Riksarkivet.

This module provides functionality to fetch and parse ALTO (Analyzed Layout and Text Object)
XML documents from the Swedish National Archives. ALTO is a standardized XML format for
storing layout and text information of scanned documents.
"""

import xml.etree.ElementTree as ET
from typing import Optional

from ..config import ALTO_NAMESPACES
from ..utils.http_client import HTTPClient


class ALTOClient:
    """
    Client for fetching and parsing ALTO XML files from Riksarkivet.

    ALTO (Analyzed Layout and Text Object) is an XML schema for describing the layout and
    content of physical text resources. This client handles multiple ALTO namespace versions
    (v2, v3, v4) and extracts full-text transcriptions from historical document scans.

    Attributes:
        http_client: HTTP client instance for making requests to ALTO XML endpoints.

    Example:
        >>> client = ALTOClient(http_client)
        >>> text = client.fetch_content("https://sok.riksarkivet.se/dokument/alto/SE_RA_123.xml")
        >>> print(text)  # Full transcribed text from the document
    """

    def __init__(self, http_client: HTTPClient):
        """
        Initialize the ALTO client.

        Args:
            http_client: Configured HTTP client for making requests.
        """
        self.http_client = http_client

    def fetch_content(self, alto_url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetch and parse an ALTO XML file to extract full text content.

        This method performs the complete workflow: fetches the XML document, parses it,
        and extracts all text content from String elements, handling multiple ALTO namespace
        versions automatically.

        Args:
            alto_url: Direct URL to the ALTO XML document.
            timeout: Request timeout in seconds (default: 10).

        Returns:
            Extracted text content as a single string with words space-separated,
            or None if fetching/parsing fails or no text is found.

        Example:
            >>> client.fetch_content("https://sok.riksarkivet.se/dokument/alto/SE_RA_123.xml")
            'Anno 1676 den 15 Januarii förekom för Rätten...'
        """
        # Fetch raw XML content
        headers = {"Accept": "application/xml, text/xml, */*"}
        xml_content = self.http_client.get_content(alto_url, timeout=timeout, headers=headers)
        if not xml_content:
            return None

        # Parse XML
        try:
            xml_root = ET.fromstring(xml_content)
        except Exception:
            return None

        # Extract and combine text
        return self._extract_text_from_alto(xml_root)

    def _extract_text_with_pattern(
        self,
        xml_root: ET.Element,
        xpath: str,
        namespaces: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Extract text content from XML using XPath pattern.

        Args:
            xml_root: Parsed XML root element.
            xpath: XPath pattern to find String elements.
            namespaces: Optional namespace dictionary for XPath query.

        Returns:
            Space-separated text from matching elements, or None if no text found.
        """
        text_segments = [
            element.get("CONTENT", "")
            for element in xml_root.findall(xpath, namespaces or {})
            if element.get("CONTENT", "")
        ]
        return " ".join(text_segments).strip() or None if text_segments else None

    def _extract_text_from_alto(self, xml_root: ET.Element) -> Optional[str]:
        """
        Extract and combine all text content from ALTO XML root element.

        Attempts to extract text using known ALTO namespaces first (v2, v3, v4),
        then falls back to namespace-less extraction if needed. Returns combined
        text from all String elements found.

        Args:
            xml_root: Parsed XML root element from ALTO document.

        Returns:
            Space-separated text from all String elements, or None if no text found.
        """
        # Try extraction with standard ALTO namespaces
        for namespace in ALTO_NAMESPACES:
            result = self._extract_text_with_pattern(xml_root, ".//alto:String", namespace)
            if result:
                return result

        # Fallback: try without namespace
        return self._extract_text_with_pattern(xml_root, ".//String")

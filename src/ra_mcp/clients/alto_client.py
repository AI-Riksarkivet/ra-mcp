"""
ALTO XML client for Riksarkivet.
"""

import xml.etree.ElementTree as ET
from typing import Optional

from ..config import ALTO_NAMESPACES
from ..utils.http_client import HTTPClient


class ALTOClient:
    """Client for fetching and parsing ALTO XML files."""

    def __init__(self):
        self.http = HTTPClient(user_agent="transcribed_search_browser/1.0")

    def fetch_content(self, alto_url: str, timeout: int = 10) -> Optional[str]:
        """Fetch and parse ALTO XML file to extract full text content."""
        xml_response_content = self._fetch_alto_xml(alto_url, timeout)
        if not xml_response_content:
            return None

        parsed_xml_root = self._parse_xml_content(xml_response_content)
        if parsed_xml_root is None:
            return None

        return self._extract_text_from_alto(parsed_xml_root)

    def _fetch_alto_xml(
        self, document_url: str, timeout_seconds: int
    ) -> Optional[bytes]:
        """Fetch ALTO XML document from URL."""
        headers = {"Accept": "application/xml, text/xml, */*"}
        return self.http.get_content(
            document_url, timeout=timeout_seconds, headers=headers
        )

    def _parse_xml_content(self, xml_content: bytes) -> Optional[ET.Element]:
        """Parse XML content into ElementTree."""
        try:
            return ET.fromstring(xml_content)
        except Exception:
            return None

    def _extract_text_from_alto(self, xml_root: ET.Element) -> Optional[str]:
        """Extract text content from ALTO XML root element."""
        extracted_text_segments = self._extract_text_with_namespaces(xml_root)

        if not extracted_text_segments:
            extracted_text_segments = self._extract_text_without_namespace(xml_root)

        return self._combine_text_segments(extracted_text_segments)

    def _extract_text_with_namespaces(self, xml_root: ET.Element) -> list:
        """Extract text using ALTO namespaces."""
        collected_text_segments = []

        for namespace_definition in ALTO_NAMESPACES:
            namespace_text_segments = self._extract_text_for_namespace(
                xml_root, namespace_definition
            )
            if namespace_text_segments:
                return namespace_text_segments

        return collected_text_segments

    def _extract_text_for_namespace(
        self, xml_root: ET.Element, namespace: dict
    ) -> list:
        """Extract text for a specific namespace."""
        text_segments = []
        string_elements = xml_root.findall(".//alto:String", namespace)

        for element in string_elements:
            text_content = self._extract_content_attribute(element)
            if text_content:
                text_segments.append(text_content)

        return text_segments

    def _extract_text_without_namespace(self, xml_root: ET.Element) -> list:
        """Extract text without namespace qualification."""
        text_segments = []
        unqualified_string_elements = xml_root.findall(".//String")

        for element in unqualified_string_elements:
            text_content = self._extract_content_attribute(element)
            if text_content:
                text_segments.append(text_content)

        return text_segments

    def _extract_content_attribute(self, element: ET.Element) -> str:
        """Extract CONTENT attribute from an element."""
        return element.get("CONTENT", "")

    def _combine_text_segments(self, text_segments: list) -> Optional[str]:
        """Combine text segments into a single string."""
        if not text_segments:
            return None

        combined_text = " ".join(text_segments)
        trimmed_text = combined_text.strip()

        return trimmed_text if trimmed_text else None

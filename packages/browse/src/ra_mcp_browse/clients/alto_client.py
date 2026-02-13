"""
ALTO XML client for Riksarkivet.

This module provides functionality to fetch and parse ALTO (Analyzed Layout and Text Object)
XML documents from the Swedish National Archives. ALTO is a standardized XML format for
storing layout and text information of scanned documents.
"""

import logging
import xml.etree.ElementTree as ET

from opentelemetry.trace import StatusCode

from ra_mcp_browse.config import ALTO_NAMESPACES
from ra_mcp_common.telemetry import get_meter, get_tracer
from ra_mcp_common.utils.http_client import HTTPClient


logger = logging.getLogger("ra_mcp.alto_client")

_tracer = get_tracer("ra_mcp.alto_client")
_meter = get_meter("ra_mcp.alto_client")
_fetch_counter = _meter.create_counter("ra_mcp.alto.fetches", description="ALTO XML fetch outcomes")


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

    def fetch_content(self, alto_url: str, timeout: int = 10) -> str | None:
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
            empty string if ALTO exists but has no text (blank page),
            or None if fetching/parsing fails (404, network error, etc.).

        Example:
            >>> client.fetch_content("https://sok.riksarkivet.se/dokument/alto/SE_RA_123.xml")
            'Anno 1676 den 15 Januarii förekom för Rätten...'
        """
        with _tracer.start_as_current_span("ALTOClient.fetch_content", attributes={"alto.url": alto_url}) as span:
            # Fetch raw XML content
            headers = {"Accept": "application/xml, text/xml, */*"}
            xml_content = self.http_client.get_content(alto_url, timeout=timeout, headers=headers)
            if not xml_content:
                span.set_attribute("alto.result", "not_found")
                _fetch_counter.add(1, {"alto.result": "not_found"})
                return None

            # Parse XML
            try:
                xml_root = ET.fromstring(xml_content)
            except Exception as e:
                logger.warning("Failed to parse ALTO XML from %s: %s", alto_url, e)
                span.set_status(StatusCode.ERROR, f"XML parse error: {e}")
                span.record_exception(e)
                span.set_attribute("alto.result", "parse_error")
                _fetch_counter.add(1, {"alto.result": "parse_error"})
                return None

            # Extract and combine text
            text = self._extract_text_from_alto(xml_root)
            result = text if text else ""
            result_type = "success" if text else "empty"
            span.set_attribute("alto.result", result_type)
            span.set_attribute("alto.text_length", len(result))
            _fetch_counter.add(1, {"alto.result": result_type})
            # Return empty string if ALTO exists but has no text (vs None for 404)
            return result

    def _extract_text_with_pattern(
        self,
        xml_root: ET.Element,
        xpath: str,
        namespaces: dict | None = None,
    ) -> str | None:
        """
        Extract text content from XML using XPath pattern.

        Args:
            xml_root: Parsed XML root element.
            xpath: XPath pattern to find String elements.
            namespaces: Optional namespace dictionary for XPath query.

        Returns:
            Space-separated text from matching elements, or None if no text found.
        """
        text_segments = [element.get("CONTENT", "") for element in xml_root.findall(xpath, namespaces or {}) if element.get("CONTENT", "")]
        return " ".join(text_segments).strip() or None if text_segments else None

    def _extract_text_from_alto(self, xml_root: ET.Element) -> str | None:
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

"""
ALTO XML client for Riksarkivet.

This module provides functionality to fetch and parse ALTO (Analyzed Layout and Text Object)
XML documents from the Swedish National Archives. ALTO is a standardized XML format for
storing layout and text information of scanned documents.
"""

import logging

from opentelemetry.trace import StatusCode

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_common.telemetry import get_meter, get_tracer
from ra_mcp_xml.models import TextLayer
from ra_mcp_xml.parser import detect_and_parse


logger = logging.getLogger("ra_mcp.alto_client")

_tracer = get_tracer("ra_mcp.alto_client")
_meter = get_meter("ra_mcp.alto_client")
_fetch_counter = _meter.create_counter("ra_mcp.alto.fetches", description="ALTO XML fetch outcomes")


class ALTOClient:
    """
    Client for fetching and parsing ALTO XML files from Riksarkivet.

    ALTO (Analyzed Layout and Text Object) is an XML schema for describing the layout and
    content of physical text resources. This client handles multiple ALTO namespace versions
    (v2, v3, v4) and extracts structured text layers from historical document scans.

    Attributes:
        http_client: HTTP client instance for making requests to ALTO XML endpoints.

    Example:
        >>> client = ALTOClient(http_client)
        >>> layer = client.fetch_content("https://sok.riksarkivet.se/dokument/alto/SE_RA_123.xml")
        >>> print(layer.full_text)  # Full transcribed text from the document
    """

    def __init__(self, http_client: HTTPClient):
        """
        Initialize the ALTO client.

        Args:
            http_client: Configured HTTP client for making requests.
        """
        self.http_client = http_client

    async def fetch_content(self, alto_url: str, timeout: int = 10) -> TextLayer | None:
        """
        Fetch and parse an ALTO XML file into a structured TextLayer.

        This method performs the complete workflow: fetches the XML document, parses it,
        and returns a TextLayer with line-level data (polygons, confidence, ids),
        handling multiple ALTO namespace versions automatically.

        Args:
            alto_url: Direct URL to the ALTO XML document.
            timeout: Request timeout in seconds (default: 10).

        Returns:
            TextLayer with line-level data and full_text,
            TextLayer with empty full_text if ALTO exists but has no text (blank page),
            or None if fetching/parsing fails (404, network error, etc.).

        Example:
            >>> layer = await client.fetch_content("https://sok.riksarkivet.se/dokument/alto/SE_RA_123.xml")
            >>> layer.full_text
            'Anno 1676 den 15 Januarii förekom för Rätten...'
        """
        with _tracer.start_as_current_span("ALTOClient.fetch_content", attributes={"alto.url": alto_url}) as span:
            headers = {"Accept": "application/xml, text/xml, */*"}
            raw = await self.http_client.get_content(alto_url, timeout=timeout, headers=headers)
            if not raw:
                span.set_attribute("alto.result", "not_found")
                _fetch_counter.add(1, {"alto.result": "not_found"})
                return None

            xml_content = raw.decode("utf-8") if isinstance(raw, bytes) else raw

            try:
                text_layer = detect_and_parse(xml_content)
            except Exception as e:
                logger.warning("Failed to parse ALTO XML from %s: %s", alto_url, e)
                span.set_status(StatusCode.ERROR, f"XML parse error: {e}")
                span.record_exception(e)
                span.set_attribute("alto.result", "parse_error")
                _fetch_counter.add(1, {"alto.result": "parse_error"})
                return None

            result_type = "success" if text_layer.full_text else "empty"
            span.set_attribute("alto.result", result_type)
            span.set_attribute("alto.text_length", len(text_layer.full_text))
            _fetch_counter.add(1, {"alto.result": result_type})
            return text_layer

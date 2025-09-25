"""
OAI-PMH client for Riksarkivet.
"""

from typing import Dict, Optional, Union, List

from lxml import etree

from ..config import OAI_BASE_URL, NAMESPACES
from ..utils.http_client import HTTPClient


class OAIPMHClient:
    """Client for interacting with OAI-PMH repositories."""

    def __init__(self, http_client: HTTPClient, base_url: str = OAI_BASE_URL):
        self.http_client = http_client
        self.base_url = base_url

    def get_record(
        self, identifier: str, metadata_prefix: str = "oai_ape_ead"
    ) -> Dict[str, Union[str, List, Dict]]:
        """Get a specific record with full metadata."""
        oai_request_parameters = self._build_oai_request_parameters(
            identifier, metadata_prefix
        )

        xml_response_root = self._make_request(oai_request_parameters)
        oai_record_element = self._extract_record_from_response(xml_response_root)

        extracted_record_data = self._build_basic_record_result(
            oai_record_element, metadata_prefix
        )

        if metadata_prefix == "oai_ape_ead":
            ead_metadata = self._extract_ead_metadata(oai_record_element)
            extracted_record_data.update(ead_metadata)

        return extracted_record_data

    def _build_oai_request_parameters(
        self, record_identifier: str, metadata_format: str
    ) -> Dict[str, str]:
        """Build OAI-PMH request parameters."""
        return {
            "verb": "GetRecord",
            "identifier": record_identifier,
            "metadataPrefix": metadata_format,
        }

    def _extract_record_from_response(self, xml_root: etree.Element) -> etree.Element:
        """Extract record element from OAI-PMH response."""
        record_elements = xml_root.xpath("//oai:record", namespaces=NAMESPACES)
        if not record_elements:
            raise Exception("No record found in OAI-PMH response")
        return record_elements[0]

    def _build_basic_record_result(
        self, record_element: etree.Element, metadata_format: str
    ) -> Dict[str, Union[str, List, Dict]]:
        """Build basic record result from header information."""
        record_header = self._parse_header_information(record_element)

        return {
            "identifier": record_header.get("identifier", ""),
            "datestamp": record_header.get("datestamp", ""),
            "metadata_format": metadata_format,
        }

    def _parse_header_information(
        self, record_element: etree.Element
    ) -> Dict[str, str]:
        """Parse header information from record element."""
        header_elements = record_element.xpath("oai:header", namespaces=NAMESPACES)
        if not header_elements:
            return {"identifier": "", "datestamp": ""}

        header_element = header_elements[0]
        return {
            "identifier": self._get_text(header_element, "oai:identifier") or "",
            "datestamp": self._get_text(header_element, "oai:datestamp") or "",
        }

    def extract_pid(self, identifier: str) -> Optional[str]:
        """Extract PID from a record for IIIF access."""
        try:
            retrieved_record = self.get_record(identifier, "oai_ape_ead")
            nad_link = retrieved_record.get("nad_link")

            if nad_link:
                return self._extract_pid_from_nad_link(nad_link)

            return None
        except Exception:
            return None

    def _extract_pid_from_nad_link(self, nad_link_url: str) -> str:
        """Extract PID from NAD link URL."""
        url_segments = nad_link_url.rstrip("/").split("/")
        if url_segments:
            # Remove query parameters if present
            pid = url_segments[-1].split("?")[0]
            return pid
        return ""

    def _make_request(self, request_parameters: Dict[str, str]) -> etree.Element:
        """Make an OAI-PMH request and return parsed XML using centralized HTTP client."""
        try:
            xml_content = self.http_client.get_xml(
                self.base_url, params=request_parameters, timeout=30
            )

            xml_response_root = self._parse_xml_response(xml_content)
            self._check_oai_response_errors(xml_response_root)

            return xml_response_root

        except Exception as e:
            raise Exception(f"OAI-PMH request failed: {e}") from e

    def _parse_xml_response(self, xml_data: bytes) -> etree.Element:
        """Parse XML response content."""
        try:
            return etree.fromstring(xml_data)
        except Exception as parse_error:
            raise Exception(
                f"Failed to parse XML response: {parse_error}"
            ) from parse_error

    def _check_oai_response_errors(self, xml_root: etree.Element) -> None:
        """Check for OAI-PMH errors in the response."""
        error_elements = xml_root.xpath("//oai:error", namespaces=NAMESPACES)
        if error_elements:
            error_code = error_elements[0].get("code", "unknown")
            error_message = error_elements[0].text or "No error message"
            raise Exception(f"OAI-PMH Error [{error_code}]: {error_message}")

    def _extract_ead_metadata(
        self, record_element: etree.Element
    ) -> Dict[str, Union[str, List, Dict]]:
        """Extract metadata from EAD format."""
        ead_metadata_element = self._extract_ead_element_from_record(record_element)

        if ead_metadata_element is None:
            return {}

        extracted_metadata = {}

        document_title = self._extract_title_from_ead(ead_metadata_element)
        if document_title:
            extracted_metadata["title"] = document_title

        unitid_value = self._extract_unitid_from_ead(ead_metadata_element)
        if unitid_value:
            extracted_metadata["unitid"] = unitid_value

        repository_info = self._extract_repository_from_ead(ead_metadata_element)
        if repository_info:
            extracted_metadata["repository"] = repository_info

        nad_link_url = self._extract_nad_link_from_ead(ead_metadata_element)
        if nad_link_url:
            extracted_metadata["nad_link"] = nad_link_url

        return extracted_metadata

    def _extract_ead_element_from_record(
        self, record_element: etree.Element
    ) -> Optional[etree.Element]:
        """Extract EAD element from record."""
        ead_elements = record_element.xpath(
            ".//ead:ead", namespaces={"ead": NAMESPACES["ead"]}
        )
        return ead_elements[0] if ead_elements else None

    def _extract_title_from_ead(self, ead_element: etree.Element) -> str:
        """Extract title from EAD element."""
        return (
            self._get_text(ead_element, ".//ead:unittitle", {"ead": NAMESPACES["ead"]})
            or ""
        )

    def _extract_unitid_from_ead(self, ead_element: etree.Element) -> str:
        """Extract unit ID from EAD element."""
        return (
            self._get_text(ead_element, ".//ead:unitid", {"ead": NAMESPACES["ead"]})
            or ""
        )

    def _extract_repository_from_ead(self, ead_element: etree.Element) -> str:
        """Extract repository information from EAD element."""
        return (
            self._get_text(ead_element, ".//ead:repository", {"ead": NAMESPACES["ead"]})
            or ""
        )

    def _extract_nad_link_from_ead(self, ead_element: etree.Element) -> str:
        """Extract NAD link from EAD element."""
        dao_elements = ead_element.xpath(
            ".//ead:dao", namespaces={"ead": NAMESPACES["ead"]}
        )
        if dao_elements:
            return dao_elements[0].get("{http://www.w3.org/1999/xlink}href", "")
        return ""

    def _get_text(
        self,
        element: etree.Element,
        xpath: str,
        namespaces: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Get text from element using XPath."""
        if namespaces is None:
            namespaces = NAMESPACES

        matches = element.xpath(xpath, namespaces=namespaces)
        if matches:
            if hasattr(matches[0], "text"):
                return matches[0].text
            return str(matches[0])
        return None

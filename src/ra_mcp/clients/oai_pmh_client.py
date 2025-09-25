"""
OAI-PMH client for Riksarkivet.
"""

from typing import Dict, Optional, Union, List

from lxml import etree

from ..config import OAI_BASE_URL, NAMESPACES
from ..utils import create_session


class OAIPMHClient:
    """Client for interacting with OAI-PMH repositories."""

    def __init__(self, base_url: str = OAI_BASE_URL):
        self.base_url = base_url
        self.session = create_session()

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
        return url_segments[-1] if url_segments else ""

    def _make_request(self, request_parameters: Dict[str, str]) -> etree.Element:
        """Make an OAI-PMH request and return parsed XML."""
        http_response = self.session.get(self.base_url, params=request_parameters)
        http_response.raise_for_status()

        xml_response_root = self._parse_xml_response(http_response.content)
        self._check_oai_response_errors(xml_response_root)

        return xml_response_root

    def _parse_xml_response(self, response_content: bytes) -> etree.Element:
        """Parse XML response content."""
        xml_parser = etree.XMLParser(remove_blank_text=True)
        return etree.fromstring(response_content, xml_parser)

    def _check_oai_response_errors(self, xml_root: etree.Element) -> None:
        """Check for OAI-PMH errors in response."""
        error_elements = xml_root.xpath("//oai:error", namespaces=NAMESPACES)

        if error_elements:
            error_message = self._build_error_message(error_elements[0])
            raise Exception(error_message)

    def _build_error_message(self, error_element: etree.Element) -> str:
        """Build error message from OAI-PMH error element."""
        error_code = error_element.get("code", "unknown")
        error_text = error_element.text or "Unknown error"
        return f"OAI-PMH Error [{error_code}]: {error_text}"

    def _get_text(self, element, xpath: str) -> Optional[str]:
        """Safely extract text from an XML element."""
        result = element.xpath(xpath, namespaces=NAMESPACES)
        return result[0].text if result and result[0].text else None

    def _extract_ead_metadata(
        self, record_element
    ) -> Dict[str, Union[str, List, Dict]]:
        """Extract metadata from EAD format."""
        ead_metadata_element = self._extract_ead_element_from_record(record_element)

        if not ead_metadata_element:
            return {}

        extracted_metadata = {}

        document_title = self._extract_title_from_ead(ead_metadata_element)
        if document_title:
            extracted_metadata["title"] = document_title

        document_date = self._extract_date_from_ead(ead_metadata_element)
        if document_date:
            extracted_metadata["date"] = document_date

        nad_link_url = self._extract_nad_link_from_ead(ead_metadata_element)
        if nad_link_url:
            extracted_metadata["nad_link"] = nad_link_url

        return extracted_metadata

    def _extract_ead_element_from_record(
        self, record_element: etree.Element
    ) -> Optional[etree.Element]:
        """Extract EAD element from record."""
        ead_elements = record_element.xpath(".//ead:ead", namespaces=NAMESPACES)
        return ead_elements[0] if ead_elements else None

    def _extract_title_from_ead(self, ead_element: etree.Element) -> Optional[str]:
        """Extract title from EAD element."""
        title_elements = ead_element.xpath(".//ead:unittitle", namespaces=NAMESPACES)

        if title_elements and title_elements[0].text:
            return title_elements[0].text

        return None

    def _extract_date_from_ead(self, ead_element: etree.Element) -> Optional[str]:
        """Extract date from EAD element."""
        date_elements = ead_element.xpath(".//ead:unitdate", namespaces=NAMESPACES)

        if date_elements and date_elements[0].text:
            return date_elements[0].text

        return None

    def _extract_nad_link_from_ead(self, ead_element: etree.Element) -> Optional[str]:
        """Extract NAD link from EAD element."""
        nad_reference_links = ead_element.xpath(
            ".//ead:extref/@xlink:href", namespaces=NAMESPACES
        )

        return self._find_valid_nad_link(nad_reference_links)

    def _find_valid_nad_link(self, reference_links: List[str]) -> Optional[str]:
        """Find valid NAD link from list of references."""
        valid_domains = ["sok.riksarkivet.se", "sok-acc.riksarkivet.se"]

        for link_url in reference_links:
            if any(domain in link_url for domain in valid_domains):
                return link_url

        return None

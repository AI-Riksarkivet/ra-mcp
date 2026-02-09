"""
OAI-PMH client for Riksarkivet.
"""

from typing import Dict, Optional, Union, List
import xml.etree.ElementTree as ET

from ra_mcp_common.telemetry import get_tracer
from ra_mcp_browse.config import OAI_BASE_URL, NAMESPACES
from ra_mcp_browse.models import OAIPMHMetadata
from ra_mcp_common.utils.http_client import HTTPClient

_tracer = get_tracer("ra_mcp.oai_pmh_client")


class OAIPMHClient:
    """Client for interacting with OAI-PMH repositories."""

    def __init__(self, http_client: HTTPClient, base_url: str = OAI_BASE_URL):
        self.http_client = http_client
        self.base_url = base_url

    def get_record(self, identifier: str, metadata_prefix: str = "oai_ape_ead") -> Dict[str, Union[str, List, Dict]]:
        """Get a specific record with full metadata (raw dict format)."""
        with _tracer.start_as_current_span("OAIPMHClient.get_record", attributes={"oai.identifier": identifier}):
            oai_request_parameters = self._build_oai_request_parameters(identifier, metadata_prefix)

            xml_response_root = self._make_request(oai_request_parameters)
            oai_record_element = self._extract_record_from_response(xml_response_root)

            extracted_record_data = self._build_basic_record_result(oai_record_element, metadata_prefix)

            if metadata_prefix == "oai_ape_ead":
                ead_metadata = self._extract_ead_metadata(oai_record_element)
                extracted_record_data.update(ead_metadata)

            return extracted_record_data

    def get_metadata(self, identifier: str) -> Optional[OAIPMHMetadata]:
        """Get record metadata as typed OAIPMHMetadata model."""
        with _tracer.start_as_current_span("OAIPMHClient.get_metadata", attributes={"oai.identifier": identifier}):
            try:
                record = self.get_record(identifier, "oai_ape_ead")

                # Helper to safely extract string values
                def get_str(key: str, default: Optional[str] = None) -> Optional[str]:
                    value = record.get(key, default)
                    return value if isinstance(value, str) else default

                return OAIPMHMetadata(
                    identifier=get_str("identifier", identifier) or identifier,
                    title=get_str("title"),
                    unitid=get_str("unitid"),
                    repository=get_str("repository"),
                    nad_link=get_str("nad_link"),
                    datestamp=get_str("datestamp"),
                    unitdate=get_str("unitdate"),
                    description=get_str("description"),
                    iiif_manifest=get_str("iiif_manifest"),
                    iiif_image=get_str("iiif_image"),
                )
            except Exception:
                return None

    def _build_oai_request_parameters(self, record_identifier: str, metadata_format: str) -> Dict[str, Union[str, int]]:
        """Build OAI-PMH request parameters."""
        return {
            "verb": "GetRecord",
            "identifier": record_identifier,
            "metadataPrefix": metadata_format,
        }

    def _extract_record_from_response(self, xml_root: ET.Element) -> ET.Element:
        """Extract record element from OAI-PMH response."""
        record_elements = xml_root.findall(".//{http://www.openarchives.org/OAI/2.0/}record")
        if not record_elements:
            raise Exception("No record found in OAI-PMH response")
        return record_elements[0]

    def _build_basic_record_result(self, record_element: ET.Element, metadata_format: str) -> Dict[str, Union[str, List, Dict]]:
        """Build basic record result from header information."""
        record_header = self._parse_header_information(record_element)

        return {
            "identifier": record_header.get("identifier", ""),
            "datestamp": record_header.get("datestamp", ""),
            "metadata_format": metadata_format,
        }

    def _parse_header_information(self, record_element: ET.Element) -> Dict[str, str]:
        """Parse header information from record element."""
        oai_ns = "{http://www.openarchives.org/OAI/2.0/}"
        header_elements = record_element.findall(f"./{oai_ns}header")
        if not header_elements:
            return {"identifier": "", "datestamp": ""}

        header_element = header_elements[0]
        return {
            "identifier": self._get_text(header_element, f"{oai_ns}identifier") or "",
            "datestamp": self._get_text(header_element, f"{oai_ns}datestamp") or "",
        }

    def extract_manifest_id(self, identifier: str) -> Optional[str]:
        """Extract PID from a record for IIIF access."""
        with _tracer.start_as_current_span("OAIPMHClient.extract_manifest_id", attributes={"oai.identifier": identifier}):
            try:
                # Use typed metadata to get nad_link safely
                metadata = self.get_metadata(identifier)
                if metadata and metadata.nad_link:
                    return self._extract_manifest_id_from_nad_link(metadata.nad_link)
                return None
            except Exception:
                return None

    def _extract_manifest_id_from_nad_link(self, nad_link_url: str) -> str:
        """Extract Manifest ID from NAD link URL."""
        url_segments = nad_link_url.rstrip("/").split("/")
        if url_segments:
            # Remove query parameters if present
            manifest_id = url_segments[-1].split("?")[0]

            return manifest_id
        return ""

    def _make_request(self, request_parameters: Dict[str, Union[str, int]]) -> ET.Element:
        """Make an OAI-PMH request and return parsed XML using centralized HTTP client."""
        try:
            xml_content = self.http_client.get_xml(self.base_url, params=request_parameters, timeout=30)

            xml_response_root = self._parse_xml_response(xml_content)
            self._check_oai_response_errors(xml_response_root)

            return xml_response_root

        except Exception as e:
            raise Exception(f"OAI-PMH request failed: {e}") from e

    def _parse_xml_response(self, xml_data: bytes) -> ET.Element:
        """Parse XML response content."""
        try:
            return ET.fromstring(xml_data)
        except Exception as parse_error:
            raise Exception(f"Failed to parse XML response: {parse_error}") from parse_error

    def _check_oai_response_errors(self, xml_root: ET.Element) -> None:
        """Check for OAI-PMH errors in the response."""
        error_elements = xml_root.findall(".//{http://www.openarchives.org/OAI/2.0/}error")
        if error_elements:
            error_code = error_elements[0].get("code", "unknown")
            error_message = error_elements[0].text or "No error message"
            raise Exception(f"OAI-PMH Error [{error_code}]: {error_message}")

    def _extract_ead_metadata(self, record_element: ET.Element) -> Dict[str, Union[str, List, Dict]]:
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

        unitdate_value = self._extract_unitdate_from_ead(ead_metadata_element)
        if unitdate_value:
            extracted_metadata["unitdate"] = unitdate_value

        description_text = self._extract_description_from_ead(ead_metadata_element)
        if description_text:
            extracted_metadata["description"] = description_text

        iiif_manifest_url = self._extract_iiif_manifest_from_ead(ead_metadata_element)
        if iiif_manifest_url:
            extracted_metadata["iiif_manifest"] = iiif_manifest_url

        iiif_image_url = self._extract_iiif_image_from_ead(ead_metadata_element)
        if iiif_image_url:
            extracted_metadata["iiif_image"] = iiif_image_url

        return extracted_metadata

    def _extract_ead_element_from_record(self, record_element: ET.Element) -> Optional[ET.Element]:
        """Extract EAD element from record."""
        ead_ns = NAMESPACES["ead"]
        ead_elements = record_element.findall(f".//{{{ead_ns}}}ead")
        return ead_elements[0] if ead_elements else None

    def _extract_title_from_ead(self, ead_element: ET.Element) -> str:
        """Extract title from EAD element."""
        ead_ns = NAMESPACES["ead"]
        return self._get_text(ead_element, f".//{{{ead_ns}}}unittitle") or ""

    def _extract_unitid_from_ead(self, ead_element: ET.Element) -> str:
        """Extract unit ID from EAD element."""
        ead_ns = NAMESPACES["ead"]
        return self._get_text(ead_element, f".//{{{ead_ns}}}unitid") or ""

    def _extract_repository_from_ead(self, ead_element: ET.Element) -> str:
        """Extract repository information from EAD element."""
        ead_ns = NAMESPACES["ead"]
        return self._get_text(ead_element, f".//{{{ead_ns}}}repository") or ""

    def _extract_nad_link_from_ead(self, ead_element: ET.Element) -> str:
        """Extract NAD link from EAD element (dao with xlink:role='TEXT')."""
        ead_ns = NAMESPACES["ead"]
        xlink_ns = "{http://www.w3.org/1999/xlink}"
        dao_elements = ead_element.findall(f".//{{{ead_ns}}}dao")
        for dao in dao_elements:
            if dao.get(f"{xlink_ns}role") == "TEXT":
                return dao.get(f"{xlink_ns}href", "")
        # Fallback to first dao if no TEXT role found
        if dao_elements:
            return dao_elements[0].get(f"{xlink_ns}href", "")
        return ""

    def _extract_unitdate_from_ead(self, ead_element: ET.Element) -> str:
        """Extract unit date from EAD element."""
        ead_ns = NAMESPACES["ead"]
        return self._get_text(ead_element, f".//{{{ead_ns}}}unitdate") or ""

    def _extract_description_from_ead(self, ead_element: ET.Element) -> str:
        """Extract description/scopecontent from EAD element."""
        ead_ns = NAMESPACES["ead"]
        # scopecontent contains paragraphs, get all text
        scopecontent_elements = ead_element.findall(f".//{{{ead_ns}}}scopecontent")
        if scopecontent_elements:
            # Get all paragraph text within scopecontent
            paragraphs = scopecontent_elements[0].findall(f".//{{{ead_ns}}}p")
            if paragraphs:
                return " ".join(p.text for p in paragraphs if p.text)
        return ""

    def _extract_iiif_manifest_from_ead(self, ead_element: ET.Element) -> str:
        """Extract IIIF manifest URL from EAD element (dao with xlink:role='MANIFEST')."""
        ead_ns = NAMESPACES["ead"]
        xlink_ns = "{http://www.w3.org/1999/xlink}"
        dao_elements = ead_element.findall(f".//{{{ead_ns}}}dao")
        for dao in dao_elements:
            if dao.get(f"{xlink_ns}role") == "MANIFEST":
                return dao.get(f"{xlink_ns}href", "")
        return ""

    def _extract_iiif_image_from_ead(self, ead_element: ET.Element) -> str:
        """Extract IIIF image URL from EAD element (dao with xlink:role='IMAGE')."""
        ead_ns = NAMESPACES["ead"]
        xlink_ns = "{http://www.w3.org/1999/xlink}"
        dao_elements = ead_element.findall(f".//{{{ead_ns}}}dao")
        for dao in dao_elements:
            if dao.get(f"{xlink_ns}role") == "IMAGE":
                return dao.get(f"{xlink_ns}href", "")
        return ""

    def _get_text(
        self,
        element: ET.Element,
        tag_path: str,
    ) -> Optional[str]:
        """Get text from element using tag path (with namespace)."""
        matches = element.findall(tag_path)
        if matches and matches[0].text:
            return matches[0].text
        return None

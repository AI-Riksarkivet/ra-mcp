"""
OAI-PMH client for Riksarkivet.
"""

import logging
import xml.etree.ElementTree as ET

from opentelemetry.trace import StatusCode

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_common.telemetry import get_meter, get_tracer
from ra_mcp_oai_pmh_lib.config import NAMESPACES, OAI_BASE_URL
from ra_mcp_oai_pmh_lib.models import OAIPMHMetadata


logger = logging.getLogger("ra_mcp.oai_pmh_client")

_tracer = get_tracer("ra_mcp.oai_pmh_client")
_meter = get_meter("ra_mcp.oai_pmh_client")
_fetch_counter = _meter.create_counter("ra_mcp.oai_pmh.fetches", description="OAI-PMH metadata fetch outcomes")

_OAI_NS = NAMESPACES["oai"]
_EAD_NS = NAMESPACES["ead"]
_XLINK_NS = NAMESPACES["xlink"]


class OAIPMHClient:
    """Client for interacting with OAI-PMH repositories."""

    def __init__(self, http_client: HTTPClient, base_url: str = OAI_BASE_URL):
        self.http_client = http_client
        self.base_url = base_url

    async def get_metadata(self, identifier: str) -> OAIPMHMetadata | None:
        """Get record metadata as typed OAIPMHMetadata model.

        Fetches the OAI-PMH GetRecord response for the given identifier and
        parses the EAD metadata into a structured model.

        Args:
            identifier: Record identifier (e.g., "SE/RA/310187/1").

        Returns:
            Parsed metadata, or None on fetch/parse failure.
        """
        with _tracer.start_as_current_span("OAIPMHClient.get_metadata", attributes={"oai.identifier": identifier}) as span:
            try:
                params: dict[str, str | int] = {"verb": "GetRecord", "identifier": identifier, "metadataPrefix": "oai_ape_ead"}
                xml_root = await self._make_request(params)
                record = self._extract_record(xml_root)

                header_id, datestamp = self._parse_header(record)
                metadata = self._parse_ead_metadata(record, header_id or identifier, datestamp)

                _fetch_counter.add(1, {"oai_pmh.result": "success"})
                return metadata
            except Exception as e:
                logger.warning("Failed to get OAI-PMH metadata for %s: %s", identifier, e)
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                _fetch_counter.add(1, {"oai_pmh.result": "error"})
                return None

    async def extract_manifest_id(self, identifier: str) -> str | None:
        """Extract PID from a record for IIIF access."""
        with _tracer.start_as_current_span("OAIPMHClient.extract_manifest_id", attributes={"oai.identifier": identifier}) as span:
            try:
                metadata = await self.get_metadata(identifier)
                return self.manifest_id_from_metadata(metadata)
            except Exception as e:
                logger.warning("Failed to extract manifest ID for %s: %s", identifier, e)
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                return None

    def manifest_id_from_metadata(self, metadata: OAIPMHMetadata | None) -> str | None:
        """Extract manifest ID from already-fetched metadata (no HTTP call)."""
        if metadata and metadata.nad_link:
            return self._extract_manifest_id_from_nad_link(metadata.nad_link)
        return None

    def _extract_manifest_id_from_nad_link(self, nad_link_url: str) -> str:
        """Extract Manifest ID from NAD link URL."""
        url_segments = nad_link_url.rstrip("/").split("/")
        if url_segments:
            return url_segments[-1].split("?")[0]
        return ""

    # -- XML request / response helpers --

    async def _make_request(self, params: dict[str, str | int]) -> ET.Element:
        """Make an OAI-PMH request and return parsed XML."""
        try:
            xml_bytes = await self.http_client.get_xml(self.base_url, params=params, timeout=30)
            xml_root = ET.fromstring(xml_bytes)
            self._check_oai_errors(xml_root)
            return xml_root
        except Exception as e:
            raise Exception(f"OAI-PMH request failed: {e}") from e

    def _check_oai_errors(self, xml_root: ET.Element) -> None:
        """Raise on OAI-PMH error responses."""
        error = xml_root.find(f".//{{{_OAI_NS}}}error")
        if error is not None:
            code = error.get("code", "unknown")
            message = error.text or "No error message"
            raise Exception(f"OAI-PMH Error [{code}]: {message}")

    def _extract_record(self, xml_root: ET.Element) -> ET.Element:
        """Extract the <record> element from an OAI-PMH response."""
        record = xml_root.find(f".//{{{_OAI_NS}}}record")
        if record is None:
            raise Exception("No record found in OAI-PMH response")
        return record

    # -- Header parsing --

    def _parse_header(self, record: ET.Element) -> tuple[str, str]:
        """Parse header, returning (identifier, datestamp)."""
        header = record.find(f"./{{{_OAI_NS}}}header")
        if header is None:
            return "", ""
        identifier = self._text(header, f"{{{_OAI_NS}}}identifier") or ""
        datestamp = self._text(header, f"{{{_OAI_NS}}}datestamp") or ""
        return identifier, datestamp

    # -- EAD metadata parsing --

    def _parse_ead_metadata(self, record: ET.Element, identifier: str, datestamp: str) -> OAIPMHMetadata:
        """Parse EAD metadata from a record element into OAIPMHMetadata."""
        ead = record.find(f".//{{{_EAD_NS}}}ead")
        if ead is None:
            return OAIPMHMetadata(identifier=identifier, datestamp=datestamp or None)

        return OAIPMHMetadata(
            identifier=identifier,
            datestamp=datestamp or None,
            title=self._text(ead, f".//{{{_EAD_NS}}}unittitle") or None,
            unitid=self._text(ead, f".//{{{_EAD_NS}}}unitid") or None,
            repository=self._text(ead, f".//{{{_EAD_NS}}}repository") or None,
            nad_link=self._dao_href(ead, "TEXT"),
            unitdate=self._text(ead, f".//{{{_EAD_NS}}}unitdate") or None,
            description=self._scopecontent_text(ead),
            iiif_manifest=self._dao_href(ead, "MANIFEST"),
            iiif_image=self._dao_href(ead, "IMAGE"),
        )

    def _dao_href(self, ead: ET.Element, role: str) -> str | None:
        """Extract xlink:href from a <dao> with the given xlink:role.

        Falls back to the first <dao> when *role* is ``"TEXT"`` and no
        explicit TEXT dao exists.
        """
        xlink_role = f"{{{_XLINK_NS}}}role"
        xlink_href = f"{{{_XLINK_NS}}}href"
        dao_elements = ead.findall(f".//{{{_EAD_NS}}}dao")
        for dao in dao_elements:
            if dao.get(xlink_role) == role:
                return dao.get(xlink_href) or None
        # Fallback to first dao for TEXT role only
        if role == "TEXT" and dao_elements:
            return dao_elements[0].get(xlink_href) or None
        return None

    def _scopecontent_text(self, ead: ET.Element) -> str | None:
        """Join paragraph text from <scopecontent>."""
        sc = ead.find(f".//{{{_EAD_NS}}}scopecontent")
        if sc is None:
            return None
        paragraphs = sc.findall(f".//{{{_EAD_NS}}}p")
        text = " ".join(p.text for p in paragraphs if p.text)
        return text or None

    # -- Utility --

    @staticmethod
    def _text(element: ET.Element, path: str) -> str | None:
        """Get text content of the first matching sub-element, or None."""
        match = element.find(path)
        if match is not None and match.text:
            return match.text
        return None

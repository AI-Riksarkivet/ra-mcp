"""
OAI-PMH client for Riksarkivet.
"""

from typing import Any, Dict, Optional

import requests
from lxml import etree

from ..config import OAI_BASE_URL, NAMESPACES


class OAIPMHClient:
    """Client for interacting with OAI-PMH repositories."""

    def __init__(self, base_url: str = OAI_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Transcribed-Search-Browser/1.0'})

    def get_record(self, identifier: str, metadata_prefix: str = 'oai_ape_ead') -> Dict[str, Any]:
        """Get a specific record with full metadata."""
        params = {
            'verb': 'GetRecord',
            'identifier': identifier,
            'metadataPrefix': metadata_prefix
        }

        root = self._make_request(params)
        record = root.xpath('//oai:record', namespaces=NAMESPACES)[0]
        header = record.xpath('oai:header', namespaces=NAMESPACES)[0]

        result = {
            'identifier': self._get_text(header, 'oai:identifier') or '',
            'datestamp': self._get_text(header, 'oai:datestamp') or '',
            'metadata_format': metadata_prefix
        }

        if metadata_prefix == 'oai_ape_ead':
            result.update(self._extract_ead_metadata(record))

        return result

    def extract_pid(self, identifier: str) -> Optional[str]:
        """Extract PID from a record for IIIF access."""
        try:
            record = self.get_record(identifier, 'oai_ape_ead')
            if 'nad_link' in record:
                return record['nad_link'].split('/')[-1]
            return None
        except Exception:
            return None

    def _make_request(self, params: Dict[str, str]) -> etree.Element:
        """Make an OAI-PMH request and return parsed XML."""
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()

        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(response.content, parser)

        # Check for OAI-PMH errors
        errors = root.xpath('//oai:error', namespaces=NAMESPACES)
        if errors:
            error_code = errors[0].get('code', 'unknown')
            error_msg = errors[0].text or 'Unknown error'
            raise Exception(f"OAI-PMH Error [{error_code}]: {error_msg}")

        return root

    def _get_text(self, element, xpath: str) -> Optional[str]:
        """Safely extract text from an XML element."""
        result = element.xpath(xpath, namespaces=NAMESPACES)
        return result[0].text if result and result[0].text else None

    def _extract_ead_metadata(self, record) -> Dict[str, Any]:
        """Extract metadata from EAD format."""
        metadata = {}
        ead = record.xpath('.//ead:ead', namespaces=NAMESPACES)
        if not ead:
            return metadata

        ead = ead[0]

        # Extract title
        title = ead.xpath('.//ead:unittitle', namespaces=NAMESPACES)
        if title and title[0].text:
            metadata['title'] = title[0].text

        # Extract date
        date = ead.xpath('.//ead:unitdate', namespaces=NAMESPACES)
        if date and date[0].text:
            metadata['date'] = date[0].text

        # Extract NAD link for PID
        nad_links = ead.xpath('.//ead:extref/@xlink:href', namespaces=NAMESPACES)
        if nad_links:
            for link in nad_links:
                if 'sok.riksarkivet.se' in link or 'sok-acc.riksarkivet.se' in link:
                    metadata['nad_link'] = link
                    break

        return metadata
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "requests>=2.31.0",
#     "click>=8.1.0",
#     "rich>=13.0.0",
#     "lxml>=4.9.0",
# ]
# ///

"""
Transcribed Search & Browser for Riksarkivet
Fast keyword search in transcribed materials with context display and page browsing.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from lxml import etree

# ============================================================================
# Constants and Configuration
# ============================================================================

SEARCH_API_BASE_URL = "https://data.riksarkivet.se/api/records"
COLLECTION_API_BASE_URL = "https://lbiiif.riksarkivet.se/collection/arkiv"
IIIF_BASE_URL = "https://lbiiif.riksarkivet.se"
OAI_BASE_URL = "https://oai-pmh.riksarkivet.se/OAI"
REQUEST_TIMEOUT = 60

DEFAULT_MAX_RESULTS = 50
DEFAULT_MAX_DISPLAY = 20
DEFAULT_MAX_PAGES = 10

NAMESPACES = {
    'oai': 'http://www.openarchives.org/OAI/2.0/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'ead': 'urn:isbn:1-931666-22-9',
    'xlink': 'http://www.w3.org/1999/xlink'
}

console = Console()

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SearchHit:
    """A search hit with context."""
    pid: str
    title: str
    reference_code: str
    page_number: str
    snippet_text: str
    full_page_text: Optional[str] = None
    alto_url: Optional[str] = None
    image_url: Optional[str] = None
    bildvisning_url: Optional[str] = None
    score: float = 0.0
    hierarchy: Optional[List[Dict[str, str]]] = None
    note: Optional[str] = None
    collection_url: Optional[str] = None
    manifest_url: Optional[str] = None
    archival_institution: Optional[List[Dict[str, str]]] = None
    date: Optional[str] = None

@dataclass
class PageContext:
    """Full page context around a search hit."""
    page_number: int
    page_id: str
    reference_code: str
    full_text: str
    alto_url: str
    image_url: str
    bildvisning_url: str = ""

# ============================================================================
# HTTP and API Utilities
# ============================================================================

class HTTPClient:
    """HTTP client with optimized settings for Riksarkivet APIs."""

    @staticmethod
    def create_session() -> requests.Session:
        """Create HTTP session optimized for Riksarkivet APIs."""
        session = requests.Session()
        session.headers.update({
            'Connection': 'close',
            'User-Agent': 'Transcribed-Search-Browser/1.0'
        })

        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=1, pool_maxsize=1)

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

class URLGenerator:
    """Generate various URLs for Riksarkivet resources."""

    @staticmethod
    def clean_id(pid: str) -> str:
        """Extract clean ID from PID."""
        return pid[6:] if pid.startswith('arkis!') else pid

    @staticmethod
    def format_page_number(page_number: str) -> str:
        """Format page number with proper padding."""
        clean_page = page_number.lstrip('_')
        if clean_page.isdigit():
            return f"{int(clean_page):05d}"
        return clean_page.zfill(5)

    @classmethod
    def alto_url(cls, pid: str, page_number: str) -> Optional[str]:
        """Generate ALTO URL from PID and page number."""
        try:
            manifest_id = cls.clean_id(pid)
            padded_page = cls.format_page_number(page_number)

            if len(manifest_id) >= 4:
                first_4_chars = manifest_id[:4]
                return f"https://sok.riksarkivet.se/dokument/alto/{first_4_chars}/{manifest_id}/{manifest_id}_{padded_page}.xml"
            return None
        except Exception:
            return None

    @classmethod
    def iiif_image_url(cls, pid: str, page_number: str) -> Optional[str]:
        """Generate IIIF image URL from PID and page number."""
        try:
            clean_id = cls.clean_id(pid)
            padded_page = cls.format_page_number(page_number)
            return f"https://lbiiif.riksarkivet.se/arkis!{clean_id}_{padded_page}/full/max/0/default.jpg"
        except Exception:
            return None

    @classmethod
    def bildvisning_url(cls, pid: str, page_number: str, search_term: Optional[str] = None) -> Optional[str]:
        """Generate bildvisning URL with optional search highlighting."""
        try:
            clean_id = cls.clean_id(pid)
            padded_page = cls.format_page_number(page_number)
            base_url = f"https://sok.riksarkivet.se/bildvisning/{clean_id}_{padded_page}"

            if search_term and search_term.strip():
                encoded_term = urllib.parse.quote(search_term.strip())
                return f"{base_url}#?q={encoded_term}"
            return base_url
        except Exception:
            return None

    @classmethod
    def collection_url(cls, pid: str) -> Optional[str]:
        """Generate IIIF collection URL from PID."""
        try:
            clean_id = cls.clean_id(pid)
            return f"{COLLECTION_API_BASE_URL}/{clean_id}"
        except Exception:
            return None

    @classmethod
    def manifest_url(cls, pid: str, manifest_id: Optional[str] = None) -> Optional[str]:
        """Generate IIIF manifest URL from PID and optional manifest ID."""
        try:
            clean_id = cls.clean_id(pid)
            if manifest_id:
                return f"{IIIF_BASE_URL}/{manifest_id}/manifest"
            return f"{IIIF_BASE_URL}/{clean_id}_001/manifest"
        except Exception:
            return None

# ============================================================================
# Core API Clients
# ============================================================================

class SearchAPI:
    """Client for Riksarkivet Search API."""

    def __init__(self):
        self.session = HTTPClient.create_session()

    def search_transcribed_text(self, keyword: str, max_results: int = DEFAULT_MAX_RESULTS) -> List[SearchHit]:
        """Fast search for keyword in transcribed materials."""
        console.print(f"[blue]Searching for '{keyword}' in transcribed materials...[/blue]")

        params = {
            'transcribed_text': keyword,
            'only_digitised_materials': 'true',
            'max': max_results,
            'sort': 'relevance'
        }

        try:
            response = self.session.get(SEARCH_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            hits = []
            for item in data.get('items', []):
                hits.extend(self._process_search_item(item))

            console.print(f"[green]Found {len(hits)} page-level hits in {data.get('totalHits', 0)} documents[/green]")
            return hits

        except Exception as e:
            console.print(f"[red]Search failed: {e}[/red]")
            return []

    def _process_search_item(self, item: Dict[str, Any]) -> List[SearchHit]:
        """Process a single search result item into SearchHit objects."""
        metadata = item.get('metadata', {})
        transcribed_data = item.get('transcribedText', {})

        # Extract basic info
        pid = item.get('id', 'Unknown')
        title = item.get('caption', '(No title)')
        reference_code = metadata.get('referenceCode', '')

        # Extract enhanced metadata
        hierarchy = metadata.get('hierarchy', [])
        note = metadata.get('note')
        archival_institution = metadata.get('archivalInstitution', [])
        date = metadata.get('date')

        # Generate URLs
        collection_url = URLGenerator.collection_url(pid) if pid else None
        manifest_url = URLGenerator.manifest_url(pid) if pid else None

        hits = []
        if transcribed_data and 'snippets' in transcribed_data:
            for snippet in transcribed_data['snippets']:
                pages = snippet.get('pages', [])
                for page in pages:
                    page_id = page.get('id', '').lstrip('_') if isinstance(page, dict) else str(page)

                    hit = SearchHit(
                        pid=pid,
                        title=title[:100] + '...' if len(title) > 100 else title,
                        reference_code=reference_code,
                        page_number=page_id,
                        snippet_text=self._clean_html(snippet.get('text', '')),
                        score=snippet.get('score', 0),
                        hierarchy=hierarchy,
                        note=note,
                        collection_url=collection_url,
                        manifest_url=manifest_url,
                        archival_institution=archival_institution,
                        date=date
                    )
                    hits.append(hit)
        return hits

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove HTML tags from text."""
        import re
        return re.sub(r'<[^>]+>', '', text)

class ALTOClient:
    """Client for fetching and parsing ALTO XML files."""

    def __init__(self):
        self.session = HTTPClient.create_session()

    def fetch_content(self, alto_url: str, timeout: int = 10) -> Optional[str]:
        """Fetch and parse ALTO XML file to extract full text content."""
        try:
            headers = {
                'User-Agent': 'transcribed_search_browser/1.0',
                'Accept': 'application/xml, text/xml, */*'
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
        # Try different ALTO namespaces
        namespaces = [
            {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'},
            {'alto': 'http://www.loc.gov/standards/alto/ns-v2#'},
            {'alto': 'http://www.loc.gov/standards/alto/ns-v3#'},
        ]

        text_lines = []

        # Try with namespaces first
        for ns in namespaces:
            for string_elem in root.findall('.//alto:String', ns):
                content = string_elem.get('CONTENT', '')
                if content:
                    text_lines.append(content)
            if text_lines:
                break

        # If no namespace works, try without namespace
        if not text_lines:
            for string_elem in root.findall('.//String'):
                content = string_elem.get('CONTENT', '')
                if content:
                    text_lines.append(content)

        full_text = ' '.join(text_lines)
        return full_text.strip() if full_text else None

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

class IIIFClient:
    """Client for IIIF collections and manifests."""

    def __init__(self):
        self.session = HTTPClient.create_session()

    def explore_collection(self, pid: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Explore IIIF collection to get manifests."""
        collection_url = f"{COLLECTION_API_BASE_URL}/{pid}"

        try:
            response = self.session.get(collection_url, timeout=timeout)
            if response.status_code == 404:
                return None

            response.raise_for_status()
            data = response.json()

            title = self._extract_iiif_label(data.get('label', {}), "Unknown Collection")

            manifests = []
            for item in data.get('items', []):
                if item.get('type') == 'Manifest':
                    manifest_title = self._extract_iiif_label(item.get('label', {}), "Untitled")
                    manifest_url = item.get('id', '')
                    manifest_id = manifest_url.rstrip('/').split('/')[-2] if '/manifest' in manifest_url else manifest_url.split('/')[-1]

                    manifests.append({
                        'id': manifest_id or manifest_url,
                        'label': manifest_title,
                        'url': manifest_url
                    })

            return {
                'title': title,
                'manifests': manifests,
                'collection_url': collection_url
            }

        except Exception:
            return None

    @staticmethod
    def _extract_iiif_label(label_obj: Any, default: str = "Unknown") -> str:
        """Smart IIIF label extraction supporting all language map formats."""
        if not label_obj:
            return default

        if isinstance(label_obj, str):
            return label_obj

        if isinstance(label_obj, dict):
            for lang in ['sv', 'en', 'none']:
                if lang in label_obj:
                    value = label_obj[lang]
                    return value[0] if isinstance(value, list) and value else str(value)

            first_lang = next(iter(label_obj.keys()), None)
            if first_lang:
                value = label_obj[first_lang]
                return value[0] if isinstance(value, list) and value else str(value)

        return str(label_obj) if label_obj else default

# ============================================================================
# Core Business Logic
# ============================================================================

class PageContextService:
    """Service for getting full page context."""

    def __init__(self):
        self.alto_client = ALTOClient()

    def get_page_context(self, pid: str, page_number: str, reference_code: str = "", search_term: Optional[str] = None) -> Optional[PageContext]:
        """Get full page context for a specific page."""
        alto_url = URLGenerator.alto_url(pid, page_number)
        image_url = URLGenerator.iiif_image_url(pid, page_number)
        bildvisning_url = URLGenerator.bildvisning_url(pid, page_number, search_term)

        if not alto_url:
            return None

        full_text = self.alto_client.fetch_content(alto_url)
        if not full_text:
            return None

        return PageContext(
            page_number=int(page_number) if page_number.isdigit() else 0,
            page_id=page_number,
            reference_code=reference_code,
            full_text=full_text,
            alto_url=alto_url,
            image_url=image_url or "",
            bildvisning_url=bildvisning_url or ""
        )

class SearchEnrichmentService:
    """Service for enriching search hits with full page context."""

    def __init__(self):
        self.iiif_client = IIIFClient()
        self.alto_client = ALTOClient()

    def enrich_hits_with_context(self, hits: List[SearchHit], max_pages: int = DEFAULT_MAX_PAGES, search_term: Optional[str] = None) -> List[SearchHit]:
        """Enrich search hits with full page context by exploring IIIF collections."""
        console.print(f"[blue]Fetching full page context for up to {max_pages} pages...[/blue]")

        enriched_hits = []
        processed = 0
        failed = 0

        # Group hits by PID to avoid exploring the same collection multiple times
        hits_by_pid = defaultdict(list)
        for hit in hits[:max_pages]:
            hits_by_pid[hit.pid].append(hit)

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Loading page contexts...", total=min(len(hits), max_pages))

            for pid, pid_hits in hits_by_pid.items():
                if processed >= max_pages:
                    break

                # Explore the IIIF collection to get manifest IDs
                progress.update(task, description=f"Exploring collection {pid[-8:]}...")
                collection_info = self.iiif_client.explore_collection(pid, timeout=10)

                if collection_info and collection_info.get('manifests'):
                    manifest = collection_info['manifests'][0]
                    manifest_id = manifest['id']
                    progress.update(task, description=f"Found manifest {manifest_id[-8:]}...")

                    # Process each hit for this PID
                    for hit in pid_hits:
                        if processed >= max_pages:
                            break

                        page_ref = f"{hit.reference_code or hit.pid[-8:]}:p{hit.page_number}"
                        self._enrich_single_hit(hit, manifest_id, search_term)

                        progress.update(task, description=f"Fetching {page_ref}...")

                        # Try to get ALTO content
                        if hit.alto_url:
                            full_text = self.alto_client.fetch_content(hit.alto_url, timeout=8)
                            if full_text:
                                hit.full_page_text = full_text
                                progress.update(task, description=f"✓ Loaded {page_ref} ({len(full_text)//100}/10 chars)")
                            else:
                                hit.full_page_text = hit.snippet_text
                                progress.update(task, description=f"○ Using snippet {page_ref}")
                        else:
                            hit.full_page_text = hit.snippet_text

                        enriched_hits.append(hit)
                        processed += 1
                        progress.advance(task)
                else:
                    # No manifests found, fall back to snippet text
                    for hit in pid_hits:
                        if processed >= max_pages:
                            break
                        self._enrich_single_hit(hit, hit.pid, search_term)
                        hit.full_page_text = hit.snippet_text
                        enriched_hits.append(hit)
                        processed += 1
                        failed += 1
                        progress.advance(task)

        console.print(f"[green]Successfully loaded context for {len(enriched_hits)} pages[/green]")
        if failed > 0:
            console.print(f"[yellow]Used snippet text for {failed} pages (IIIF manifests not found)[/yellow]")
        return enriched_hits

    def _enrich_single_hit(self, hit: SearchHit, manifest_id: str, search_term: Optional[str]):
        """Enrich a single hit with generated URLs."""
        hit.alto_url = URLGenerator.alto_url(manifest_id, hit.page_number)
        hit.image_url = URLGenerator.iiif_image_url(manifest_id, hit.page_number)
        hit.bildvisning_url = URLGenerator.bildvisning_url(manifest_id, hit.page_number, search_term)

    def expand_hits_with_context_padding(self, hits: List[SearchHit], padding: int = 1) -> List[SearchHit]:
        """Expand search hits with context pages around each hit."""
        if padding <= 0:
            return hits

        # Group hits by PID and reference code
        hits_by_doc = defaultdict(list)
        for hit in hits:
            key = (hit.pid, hit.reference_code)
            hits_by_doc[key].append(hit)

        expanded_hits = []

        for (pid, ref_code), doc_hits in hits_by_doc.items():
            # Get all page numbers for this document
            hit_pages = set()
            for hit in doc_hits:
                try:
                    page_num = int(hit.page_number.lstrip('0')) if hit.page_number.lstrip('0').isdigit() else int(hit.page_number)
                    hit_pages.add(page_num)
                except (ValueError, AttributeError):
                    hit_pages.add(hit.page_number)

            # Generate context pages around each hit
            context_pages = set()
            for page in hit_pages:
                if isinstance(page, int):
                    for offset in range(-padding, padding + 1):
                        context_page = page + offset
                        if context_page > 0:
                            context_pages.add(context_page)
                else:
                    context_pages.add(page)

            # Create SearchHit objects for all context pages
            for page in context_pages:
                existing_hit = self._find_existing_hit(doc_hits, page)
                if existing_hit:
                    expanded_hits.append(existing_hit)
                else:
                    context_hit = self._create_context_hit(pid, ref_code, page, doc_hits)
                    expanded_hits.append(context_hit)

        # Sort by PID, reference code, and page number
        expanded_hits.sort(key=self._sort_key)
        return expanded_hits

    def _find_existing_hit(self, doc_hits: List[SearchHit], page) -> Optional[SearchHit]:
        """Find existing hit for a given page."""
        for hit in doc_hits:
            hit_page_num = hit.page_number.lstrip('0') if hit.page_number.lstrip('0').isdigit() else hit.page_number
            try:
                if isinstance(page, int) and int(hit_page_num) == page:
                    return hit
                elif str(page) == hit.page_number:
                    return hit
            except (ValueError, AttributeError):
                if str(page) == hit.page_number:
                    return hit
        return None

    def _create_context_hit(self, pid: str, ref_code: str, page, doc_hits: List[SearchHit]) -> SearchHit:
        """Create a context hit for a page that doesn't have search results."""
        page_str = f"{page:05d}" if isinstance(page, int) else str(page)
        template_hit = doc_hits[0] if doc_hits else None

        return SearchHit(
            pid=pid,
            title=template_hit.title if template_hit else "(No title)",
            reference_code=ref_code,
            page_number=page_str,
            snippet_text="[Context page - no search hit]",
            score=0.0,
            hierarchy=template_hit.hierarchy if template_hit else None,
            note=template_hit.note if template_hit else None,
            collection_url=template_hit.collection_url if template_hit else None,
            manifest_url=template_hit.manifest_url if template_hit else None,
            archival_institution=template_hit.archival_institution if template_hit else None,
            date=template_hit.date if template_hit else None
        )

    @staticmethod
    def _sort_key(hit: SearchHit):
        """Sort key for organizing hits."""
        try:
            page_num = int(hit.page_number.lstrip('0')) if hit.page_number.lstrip('0').isdigit() else 999999
        except (ValueError, AttributeError):
            page_num = 999999
        return (hit.pid, hit.reference_code, page_num)

# ============================================================================
# Display Services
# ============================================================================

class DisplayService:
    """Service for displaying search results and page contexts."""

    @staticmethod
    def keyword_highlight(text: str, keyword: str) -> str:
        """Highlight keyword in text."""
        if not keyword:
            return text
        import re
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(lambda m: f"[bold yellow underline]{m.group()}[/bold yellow underline]", text)

    def display_search_hits(self, hits: List[SearchHit], keyword: str, max_display: int = DEFAULT_MAX_DISPLAY):
        """Display search hits in a table, grouped by reference code."""
        if not hits:
            console.print("[yellow]No search hits found.[/yellow]")
            return

        # Group hits by reference code
        from collections import OrderedDict
        grouped_hits = OrderedDict()
        for hit in hits:
            ref_code = hit.reference_code or hit.pid
            if ref_code not in grouped_hits:
                grouped_hits[ref_code] = []
            grouped_hits[ref_code].append(hit)

        console.print(f"\n✓ Found {len(hits)} page-level hits across {len(grouped_hits)} documents")
        console.print("[dim]💡 Tips: Use --context to see full page transcriptions | Use 'browse' command to view specific reference codes[/dim]")

        table = Table(
            "Institution & Reference", "Content",
            title=f"Search Results for '{keyword}'",
            show_lines=True,
            expand=True
        )

        # Display grouped results
        displayed_groups = 0
        for ref_code, ref_hits in grouped_hits.items():
            if displayed_groups >= max_display:
                break
            displayed_groups += 1

            # Take the first hit as representative for metadata
            first_hit = ref_hits[0]

            # Extract institution
            institution = ""
            if first_hit.archival_institution:
                institution = first_hit.archival_institution[0].get('caption', '') if first_hit.archival_institution else ""
            elif first_hit.hierarchy:
                institution = first_hit.hierarchy[0].get('caption', '') if first_hit.hierarchy else ""

            # Combine institution and reference with pages
            institution_and_ref = ""
            if institution:
                institution_and_ref = f"🏛️  {institution[:30] + '...' if len(institution) > 30 else institution}\n"

            # Format pages - list all pages, comma separated, with leading zeros trimmed
            pages = sorted(set(h.page_number for h in ref_hits))
            # Trim leading zeros from each page number
            pages_trimmed = []
            for p in pages:
                trimmed = p.lstrip('0') or '0'  # Keep at least one zero if all zeros
                pages_trimmed.append(trimmed)
            pages_str = ",".join(pages_trimmed)

            institution_and_ref += f"📚 \"{ref_code}\" --page \"{pages_str}\""

            if first_hit.date:
                institution_and_ref += f"\n📅 [dim]{first_hit.date}[/dim]"

            # Create content column with title and snippets from different pages
            title_text = first_hit.title[:50] + '...' if len(first_hit.title) > 50 else first_hit.title
            content_parts = []

            # Add title
            if title_text and title_text.strip():
                content_parts.append(f"[bold blue]{title_text}[/bold blue]")
            else:
                content_parts.append(f"[bright_black]No title[/bright_black]")

            # Add snippets with page numbers
            displayed_snippets = 0
            for hit in ref_hits[:3]:  # Show max 3 snippets per reference
                displayed_snippets += 1
                snippet = hit.snippet_text[:150] + '...' if len(hit.snippet_text) > 150 else hit.snippet_text
                snippet = self.keyword_highlight(snippet, keyword)
                content_parts.append(f"[dim]Page {hit.page_number}:[/dim] [italic]{snippet}[/italic]")

            if len(ref_hits) > 3:
                content_parts.append(f"[dim]...and {len(ref_hits) - 3} more pages with hits[/dim]")

            content = "\n".join(content_parts)

            table.add_row(
                institution_and_ref,
                content
            )

        console.print(table)

        # Show example browse command with actual reference from first group
        if grouped_hits:
            first_ref = next(iter(grouped_hits.keys()))
            first_group = grouped_hits[first_ref]
            pages = sorted(set(h.page_number for h in first_group))

            # Trim leading zeros from page numbers and limit to max 5 pages for example
            pages_trimmed = [p.lstrip('0') or '0' for p in pages[:5]]  # Take first 5 pages max

            console.print(f"\n[dim]💡 Example: To view these hits, run:[/dim]")
            if len(pages_trimmed) == 1:
                console.print(f"[cyan]   browse \"{first_ref}\" --page {pages_trimmed[0]} --search-term \"{keyword}\"[/cyan]")
            else:
                pages_str = ",".join(pages_trimmed)
                if len(pages) > 5:
                    console.print(f"[cyan]   browse \"{first_ref}\" --page \"{pages_str}\" --search-term \"{keyword}\"[/cyan]")
                    console.print(f"[dim]   (Showing first 5 of {len(pages)} pages with hits)[/dim]")
                else:
                    console.print(f"[cyan]   browse \"{first_ref}\" --page \"{pages_str}\" --search-term \"{keyword}\"[/cyan]")

        # Count remaining groups instead of hits
        total_groups = len(grouped_hits)
        if total_groups > displayed_groups:
            remaining_groups = total_groups - displayed_groups
            total_remaining_hits = sum(len(h) for _, h in list(grouped_hits.items())[displayed_groups:])
            console.print(f"\n[dim]... and {remaining_groups} more documents with {total_remaining_hits} hits[/dim]")
            console.print(f"[dim]Options: --max-display N to show more | --context for full pages | 'browse REFERENCE' to view specific documents[/dim]")

    def display_page_contexts(self, contexts: List[PageContext], keyword: str, reference_code: str = ""):
        """Display full page contexts with keyword highlighting."""
        if not contexts:
            console.print("[yellow]No page contexts found.[/yellow]")
            return

        console.print(f"\n[bold]Full Page Transcriptions ({len(contexts)} pages):[/bold]")

        for context in contexts:
            page_content = self._build_page_content(context, keyword, reference_code)
            panel_title = f"[cyan]Page {context.page_number}: {context.reference_code or 'Unknown Reference'}[/cyan]"
            console.print(Panel(
                "\n".join(page_content),
                title=panel_title,
                border_style="green",
                padding=(0, 1)
            ))

    def display_enriched_hits(self, hits: List[SearchHit], keyword: str, grouped: bool = False):
        """Display enriched search hits with full page context, optionally grouped by document."""
        if not hits:
            console.print("[yellow]No enriched hits found.[/yellow]")
            return

        if grouped:
            self._display_grouped_by_document(hits, keyword)
        else:
            self._display_individual_hits(hits, keyword)

    def _display_individual_hits(self, hits: List[SearchHit], keyword: str):
        """Display search hits individually."""
        console.print(f"\n[bold]Search Results with Full Page Context ({len(hits)} pages):[/bold]")

        for hit in hits:
            if not hit.full_page_text:
                continue

            page_content = self._build_hit_content(hit, keyword)
            panel_title = f"[cyan]Hit: {hit.reference_code} - Page {hit.page_number}[/cyan]"
            console.print(Panel(
                "\n".join(page_content),
                title=panel_title,
                border_style="blue",
                padding=(0, 1)
            ))

    def _display_grouped_by_document(self, hits: List[SearchHit], keyword: str):
        """Display search hits grouped by document/reference code."""
        # Group hits by reference code
        grouped_hits = defaultdict(list)
        for hit in hits:
            if hit.full_page_text:
                key = hit.reference_code or hit.pid
                grouped_hits[key].append(hit)

        console.print(f"\n[bold]Search Results Grouped by Document ({len(grouped_hits)} documents, {len(hits)} pages):[/bold]")

        for doc_ref, doc_hits in grouped_hits.items():
            # Sort pages by page number
            doc_hits.sort(key=lambda h: int(h.page_number) if h.page_number.isdigit() else 0)

            doc_content = self._build_document_content(doc_hits, keyword)
            panel_title = f"[cyan]Document: {doc_ref} ({len(doc_hits)} pages)[/cyan]"
            console.print(Panel(
                "\n".join(doc_content),
                title=panel_title,
                border_style="green",
                padding=(0, 1)
            ))

    def _build_hit_content(self, hit: SearchHit, keyword: str) -> List[str]:
        """Build content for an individual hit panel."""
        page_content = []

        # Header with metadata (reference and page info now in panel title)
        page_content.append(f"\n[bold blue]📄 Title:[/bold blue] {hit.title}")

        # Add date if available
        if hit.date:
            page_content.append(f"[bold blue]📅 Date:[/bold blue] {hit.date}")

        # Add hierarchy information
        if hit.hierarchy:
            page_content.append(f"\n[bold yellow]🏛️  Archive Hierarchy:[/bold yellow]")
            for level in hit.hierarchy:
                page_content.append(f"     📁 {level.get('caption', 'Unknown')}")

        # Add archival institution
        if hit.archival_institution:
            page_content.append(f"\n[bold yellow]🏛️  Institution:[/bold yellow]")
            for inst in hit.archival_institution:
                page_content.append(f"     🏛️  {inst.get('caption', 'Unknown')}")

        # Add note if available
        if hit.note:
            page_content.append(f"\n[bold magenta]📝 Note:[/bold magenta]")
            page_content.append(f"[italic]{hit.note}[/italic]")

        # Full transcribed text with keyword highlighting
        display_text = self.keyword_highlight(hit.full_page_text or "", keyword)
        page_content.append(f"\n[bold magenta]📜 Full Transcription:[/bold magenta]")
        page_content.append(f"[italic]{display_text}[/italic]")

        # Links section
        page_content.extend(self._build_links_section(hit))
        return page_content

    def _build_document_content(self, doc_hits: List[SearchHit], keyword: str) -> List[str]:
        """Build content for a document panel with multiple pages."""
        doc_content = []

        # Document header (reference code now in panel title)
        first_hit = doc_hits[0]
        doc_content.append(f"\n[bold blue]📄 Title:[/bold blue] {first_hit.title}")
        doc_content.append(f"[bold green]📄 Pages with hits:[/bold green] {', '.join(h.page_number for h in doc_hits)}")

        # Add document-level metadata from first hit
        if first_hit.date:
            doc_content.append(f"[bold blue]📅 Date:[/bold blue] {first_hit.date}")

        # Add hierarchy information
        if first_hit.hierarchy:
            doc_content.append(f"\n[bold yellow]🏛️  Archive Hierarchy:[/bold yellow]")
            for level in first_hit.hierarchy:
                doc_content.append(f"     📁 {level.get('caption', 'Unknown')}")

        # Add archival institution
        if first_hit.archival_institution:
            doc_content.append(f"\n[bold yellow]🏛️  Institution:[/bold yellow]")
            for inst in first_hit.archival_institution:
                doc_content.append(f"     🏛️  {inst.get('caption', 'Unknown')}")

        # Add note if available
        if first_hit.note:
            doc_content.append(f"\n[bold magenta]📝 Note:[/bold magenta]")
            doc_content.append(f"[italic]{first_hit.note}[/italic]")

        # Add document-level links
        doc_content.append(f"\n[bold cyan]🔗 Document Links:[/bold cyan]")
        if first_hit.collection_url:
            doc_content.append(f"     [dim]📚 Collection:[/dim] [link]{first_hit.collection_url}[/link]")
        if first_hit.manifest_url:
            doc_content.append(f"     [dim]📖 Manifest:[/dim] [link]{first_hit.manifest_url}[/link]")

        # Add each page's content
        for i, hit in enumerate(doc_hits, 1):
            # Mark search hits vs context pages
            is_search_hit = hit.snippet_text != "[Context page - no search hit]"
            page_marker = "🎯" if is_search_hit else "📄"
            page_type = "[bold yellow]SEARCH HIT[/bold yellow]" if is_search_hit else "[dim]context[/dim]"

            doc_content.append(f"\n[bold cyan]── {page_marker} Page {hit.page_number} ({page_type}) ──[/bold cyan]")

            # Full transcribed text with keyword highlighting
            display_text = hit.full_page_text or ""
            if keyword and is_search_hit and display_text:
                display_text = self.keyword_highlight(display_text, keyword)

            if display_text:
                doc_content.append(f"[italic]{display_text}[/italic]")
            else:
                doc_content.append(f"[dim italic]No text content available for this page[/dim italic]")

            # Links for this page
            doc_content.append(f"\n[dim]🔗 Page {hit.page_number} Links:[/dim]")
            if hit.alto_url:
                doc_content.append(f"     [dim]📝 ALTO:[/dim] [link]{hit.alto_url}[/link]")
            if hit.image_url:
                doc_content.append(f"     [dim]🖼️  Image:[/dim] [link]{hit.image_url}[/link]")
            if hit.bildvisning_url:
                doc_content.append(f"     [dim]👁️  Bildvisning:[/dim] [link]{hit.bildvisning_url}[/link]")

            # Add separator between pages (except for last page)
            if i < len(doc_hits):
                doc_content.append("")

        return doc_content

    def _build_links_section(self, hit: SearchHit) -> List[str]:
        """Build links section for a hit."""
        links = [f"\n[bold cyan]🔗 Links:[/bold cyan]"]
        if hit.alto_url:
            links.append(f"     [dim]📝 ALTO XML:[/dim] [link]{hit.alto_url}[/link]")
        if hit.image_url:
            links.append(f"     [dim]🖼️  Image:[/dim] [link]{hit.image_url}[/link]")
        if hit.bildvisning_url:
            links.append(f"     [dim]👁️  Bildvisning:[/dim] [link]{hit.bildvisning_url}[/link]")
        if hit.collection_url:
            links.append(f"     [dim]📚 Collection:[/dim] [link]{hit.collection_url}[/link]")
        if hit.manifest_url:
            links.append(f"     [dim]📖 Manifest:[/dim] [link]{hit.manifest_url}[/link]")
        return links

    def _build_page_content(self, context: PageContext, keyword: str, reference_code: str) -> List[str]:
        """Build content for a page panel."""
        page_content = []

        # Page header (page number and reference now in panel title)

        # Full transcribed text with keyword highlighting
        display_text = self.keyword_highlight(context.full_text, keyword)
        page_content.append(f"\n[bold magenta]📜 Full Transcription:[/bold magenta]")
        page_content.append(f"[italic]{display_text}[/italic]")

        # Links section
        page_content.append(f"\n[bold cyan]🔗 Links:[/bold cyan]")
        page_content.append(f"     [dim]📝 ALTO XML:[/dim] [link]{context.alto_url}[/link]")
        if context.image_url:
            page_content.append(f"     [dim]🖼️  Image:[/dim] [link]{context.image_url}[/link]")
        if context.bildvisning_url:
            page_content.append(f"     [dim]👁️  Bildvisning:[/dim] [link]{context.bildvisning_url}[/link]")

        return page_content

# ============================================================================
# Utility Functions
# ============================================================================

def parse_page_range(page_range: Optional[str], total_pages: int = 1000) -> List[int]:
    """Parse page range string and return list of page numbers."""
    if not page_range:
        return list(range(1, min(total_pages + 1, 21)))  # Default to first 20 pages

    pages = []
    parts = page_range.split(',')

    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            start = int(start.strip())
            end = int(end.strip())
            pages.extend(range(start, min(end + 1, total_pages + 1)))
        else:
            page_num = int(part.strip())
            if 1 <= page_num <= total_pages:
                pages.append(page_num)

    return sorted(list(set(pages)))

# ============================================================================
# CLI Interface
# ============================================================================

@click.group()
def cli():
    """Transcribed Search & Browser for Riksarkivet.

    Commands:
      search     - Search for keywords in transcribed materials
      browse     - Browse pages by reference code
      show-pages - Search and display exact pages with context

    Quick Start:
      search "keyword"                    - Basic search
      search "keyword" --context          - Search with full page transcriptions
      browse "SE/RA/123" --page 5         - View specific page
    """
    pass

@cli.command()
@click.argument('keyword')
@click.option('--max', 'max_results', type=int, default=DEFAULT_MAX_RESULTS, help='Maximum search results')
@click.option('--max-display', type=int, default=DEFAULT_MAX_DISPLAY, help='Maximum results to display')
@click.option('--context', is_flag=True, help='Show full page context for search hits')
@click.option('--max-pages', type=int, default=DEFAULT_MAX_PAGES, help='Maximum pages to load context for')
@click.option('--no-grouping', is_flag=True, help='Show pages individually instead of grouped by document (only with --context)')
def search(keyword: str, max_results: int, max_display: int, context: bool, max_pages: int, no_grouping: bool):
    """Search for keyword in transcribed materials.

    Fast search across all transcribed documents in Riksarkivet.
    Returns reference codes and page numbers containing the keyword.

    Examples:
        uv run transcribed_search_browser.py search "Stockholm"
        uv run transcribed_search_browser.py search "trolldom" --context --max-pages 5
        uv run transcribed_search_browser.py search "vasa" --context --no-grouping --max-pages 3
    """
    search_api = SearchAPI()
    display_service = DisplayService()

    hits = search_api.search_transcribed_text(keyword, max_results)

    if context and hits:
        enrichment_service = SearchEnrichmentService()
        enriched_hits = enrichment_service.enrich_hits_with_context(hits, max_pages, keyword)
        # Display enriched hits with full transcriptions
        display_service.display_enriched_hits(enriched_hits, keyword, grouped=not no_grouping)
    else:
        display_service.display_search_hits(hits, keyword, max_display)

@cli.command()
@click.argument('keyword')
@click.option('--max-pages', type=int, default=DEFAULT_MAX_PAGES, help='Maximum pages to display with full context')
@click.option('--context-padding', type=int, default=1, help='Number of pages to include before and after each hit for context')
@click.option('--no-grouping', is_flag=True, help='Show pages individually instead of grouped by document')
def show_pages(keyword: str, max_pages: int, context_padding: int, no_grouping: bool):
    """Search for keyword and show the exact pages containing it with context.

    This combines search and browse - finds pages with the keyword then displays
    the full page transcriptions with the keyword highlighted, plus surrounding
    pages for context. Results are grouped by document by default for better context.

    Examples:
        uv run transcribed_search_browser.py show-pages "Stockholm" --max-pages 5
        uv run transcribed_search_browser.py show-pages "trolldom" --no-grouping
        uv run transcribed_search_browser.py show-pages "vasa" --context-padding 2
    """
    # Step 1: Search for the keyword
    search_limit = max(max_pages * 3, 50)  # Get more results to have options
    console.print(f"[blue]Searching for '{keyword}' to find exact pages...[/blue]")

    search_api = SearchAPI()
    hits = search_api.search_transcribed_text(keyword, search_limit)

    if not hits:
        console.print("[yellow]No pages found containing the keyword.[/yellow]")
        return

    # Step 2: Show basic search results first
    console.print(f"\n[green]Found {len(hits)} pages containing '{keyword}'[/green]")

    # Limit to max_pages for detailed display
    display_hits = hits[:max_pages]
    console.print(f"[blue]Showing full context for first {len(display_hits)} pages...[/blue]")

    # Step 3: Expand hits with context padding and enrich with full page context
    enrichment_service = SearchEnrichmentService()
    expanded_hits = enrichment_service.expand_hits_with_context_padding(display_hits, context_padding)
    console.print(f"[blue]Expanded to {len(expanded_hits)} pages including context padding (+/- {context_padding} pages)...[/blue]")

    enriched_hits = enrichment_service.enrich_hits_with_context(expanded_hits, len(expanded_hits), keyword)

    # Step 4: Display results (grouped by document by default)
    display_service = DisplayService()
    if enriched_hits:
        # Use grouped=True by default unless --no-grouping is specified
        display_service.display_enriched_hits(enriched_hits, keyword, grouped=not no_grouping)
    else:
        console.print("[red]No page transcriptions could be loaded.[/red]")

@cli.command()
@click.argument('reference_code')
@click.option('--pages', help='Page range to display (e.g., "1-10" or "5,7,9")')
@click.option('--page', help='Single page or page range to display (alias for --pages)')
@click.option('--search-term', help='Highlight this term in the text')
@click.option('--max-display', type=int, default=DEFAULT_MAX_DISPLAY, help='Maximum pages to display')
def browse(reference_code: str, pages: Optional[str], page: Optional[str], search_term: Optional[str], max_display: int):
    """Browse pages by reference code.

    You can specify pages using either --pages or --page (they work the same way).
    If both are provided, --page takes precedence.

    Examples:
        uv run transcribed_search_browser.py browse "SE/RA/123" --page 5
        uv run transcribed_search_browser.py browse "SE/RA/123" --pages "1-10"
        uv run transcribed_search_browser.py browse "SE/RA/123" --page "5,7,9"
    """
    console.print(f"[blue]Looking up reference code: {reference_code}[/blue]")

    # Handle both --pages and --page options (--page takes precedence if both are provided)
    page_range = page if page is not None else pages

    # Try search API first
    session = HTTPClient.create_session()
    pid = None

    try:
        params = {'reference_code': reference_code, 'only_digitised_materials': 'true', 'max': 1}
        response = session.get(SEARCH_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if data.get('items'):
            pid = data['items'][0].get('id')
            console.print(f"[green]Found PID via search: {pid}[/green]")
    except Exception as e:
        console.print(f"[yellow]Search API lookup failed: {e}[/yellow]")

    # Fall back to OAI-PMH
    if not pid:
        console.print(f"[blue]Trying OAI-PMH lookup...[/blue]")
        oai_client = OAIPMHClient()
        try:
            pid = oai_client.extract_pid(reference_code)
            if pid:
                console.print(f"[green]Found PID via OAI-PMH: {pid}[/green]")
            else:
                console.print(f"[red]Could not extract PID for {reference_code}[/red]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error getting OAI-PMH record: {e}[/red]")
            sys.exit(1)

    # Get manifest and load pages
    iiif_client = IIIFClient()
    collection_info = iiif_client.explore_collection(pid)

    manifest_id = pid
    if collection_info and collection_info.get('manifests'):
        manifest_id = collection_info['manifests'][0]['id']
        console.print(f"[green]Found manifest: {manifest_id}[/green]")

    selected_pages = parse_page_range(page_range)
    console.print(f"[blue]Loading {len(selected_pages[:max_display])} pages...[/blue]")

    # Load page contexts
    page_service = PageContextService()
    display_service = DisplayService()
    contexts = []

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Loading page contexts...", total=len(selected_pages[:max_display]))

        for page_num in selected_pages[:max_display]:
            progress.update(task, description=f"Loading page {page_num}...")
            context = page_service.get_page_context(manifest_id, str(page_num), reference_code, search_term)
            if context:
                contexts.append(context)
                progress.update(task, description=f"✓ Loaded page {page_num}")
            else:
                progress.update(task, description=f"✗ Failed to load page {page_num}")
            progress.advance(task)

    display_service.display_page_contexts(contexts, search_term or "", reference_code)
    console.print(f"\n[green]Successfully loaded {len(contexts)} pages[/green]")

if __name__ == '__main__':
    cli()
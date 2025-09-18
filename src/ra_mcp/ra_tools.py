"""
MCP tool definitions for RA-MCP server.
Provides search and browse functionality for Riksarkivet documents.
"""

from typing import Optional, List
from fastmcp import FastMCP
from pydantic import Field

from ra_core import (
    SearchAPI,
    SearchEnrichmentService,
    PageContextService,
    IIIFClient,
    HTTPClient,
    OAIPMHClient,
    SEARCH_API_BASE_URL,
    REQUEST_TIMEOUT,
    parse_page_range
)
from formatters import (
    format_search_results,
    format_page_contexts,
    format_document_structure,
    format_error
)
from cache import get_cache
import os


# Initialize FastMCP instance
ra_mcp = FastMCP(
    name="ra-mcp",
    instructions="""
    🏛️ Riksarkivet (RA) Search and Browse MCP Server

    This server provides access to transcribed historical documents from the Swedish National Archives.

    AVAILABLE TOOLS:

    1. 🔍 search_transcribed - Search for keywords in transcribed materials
       - Returns documents and pages containing the keyword
       - Offset parameter required to encourage comprehensive discovery
       - Context disabled by default for maximum hit coverage
       - Provides direct links to images and ALTO XML

    2. 📖 browse_document - Browse specific pages by reference code
       - View full transcriptions of specific pages
       - Supports page ranges and multiple pages
       - Optional keyword highlighting

    3. 📚 get_document_structure - Get document structure without content
       - Quick overview of available manifests
       - Document metadata and hierarchy
       - Useful for understanding what's available

    SEARCH STRATEGY FOR MAXIMUM DISCOVERY:
    1. Start with search_transcribed(keyword, offset=0) for initial hits
    2. Continue pagination with increasing offsets (50, 100, 150...) to find all matches
    3. Use show_context=False (default) to see more results per query
    4. Only enable show_context=True when you want full page text for specific hits
    5. EXPLORE RELATED TERMS: Search for similar/related words to gather comprehensive context
       - Historical variants and spellings (e.g., "trolldom" + "häxa" + "trollkona")
       - Synonyms and related concepts (e.g., "satan" + "djävul" for devil-related terms)
       - Different word forms (e.g., "trolleri" + "trollkonst" for witchcraft variants)
       - Period-appropriate terminology and archaic spellings
    6. Note reference codes and page numbers for detailed browsing
    7. Use browse_document() to view full transcriptions of interesting pages

    TYPICAL WORKFLOW:
    1. Comprehensive search: search_transcribed(term, 0), then search_transcribed(term, 50), etc.
    2. Search related terms in parallel to build complete context
    3. Review hit summaries to identify most relevant documents across all searches
    4. Use browse_document() for detailed examination of specific pages
    5. Use get_document_structure() to understand document organization

    All tools return rich, formatted text optimized for LLM understanding.
    """,
)


@ra_mcp.tool(
    name="search_transcribed",
    description="Search for keywords in transcribed historical documents from Riksarkivet"
)
async def search_transcribed(
    keyword: str,
    offset: int,
    show_context: bool = False,
    max_results: int = 10,
    max_hits_per_document: int = 3,
    max_pages_with_context: int = 0,
    context_padding: int = 0,
    max_response_tokens: int = 15000,
    truncate_page_text: int = 800
) -> str:
    """
    Search for keywords in transcribed materials from the Swedish National Archives.

    Returns rich formatted text with:
    - Full page transcriptions with keyword highlighting
    - Document metadata and hierarchy
    - Direct links to images and transcriptions
    - Context pages around each hit for better understanding

    Parameters:
    - keyword: The search term
    - offset: Start position in search results for pagination (required for more hits)
    - show_context: Include full page text (default False)
    - max_results: Maximum number of documents to fetch (default 10)
    - max_hits_per_document: Maximum page hits to return per document (default 3)
    - max_pages_with_context: Maximum pages to enrich with full text (default 0)
    - context_padding: Pages of context around each hit (default 0)
    - max_response_tokens: Approximate max tokens in response to prevent overflow (default 15000)
    - truncate_page_text: Max characters per page text to prevent huge responses (default 800)

    Example:
    - search_transcribed("häxor", offset=0) - Find documents about witches
    - search_transcribed("Stockholm", offset=0, show_context=True, max_pages_with_context=10) - Find Stockholm references with context
    - search_transcribed("näcken", offset=10, max_results=10) - Get results 11-20
    - search_transcribed("näcken", offset=0, max_pages_with_context=3, context_padding=0) - Limit response size
    """
    try:
        cache = get_cache()

        # Check cache for search results
        cache_params = {'keyword': keyword, 'max_results': max_results, 'offset': offset, 'max_hits_per_document': max_hits_per_document}
        cached_hits = cache.get('search', cache_params)

        if cached_hits is None:
            # Perform fresh search
            search_api = SearchAPI()
            hits, total_hits = search_api.search_transcribed_text(keyword, max_results, offset, max_hits_per_document)

            # Cache the search results
            cache.set('search', cache_params, (hits, total_hits))
        else:
            hits, total_hits = cached_hits

        if not hits:
            if offset > 0:
                return f"No more results found for '{keyword}' at offset {offset}. Total results: {total_hits if 'total_hits' in locals() else 'unknown'}"
            return f"No results found for '{keyword}'. Try different search terms or variations."

        # Enrich with context if requested
        if show_context and hits:
            enrichment_service = SearchEnrichmentService()

            # Limit hits to max_pages_with_context
            hits_to_enrich = hits[:max_pages_with_context]

            # Expand with context padding if requested
            if context_padding > 0:
                hits_to_enrich = enrichment_service.expand_hits_with_context_padding(
                    hits_to_enrich, context_padding
                )

            # Enrich with full page text
            enriched_hits = enrichment_service.enrich_hits_with_context(
                hits_to_enrich,
                len(hits_to_enrich),
                keyword
            )

            # Apply text truncation if needed to prevent token overflow
            for hit in enriched_hits:
                if hasattr(hit, 'full_page_text') and hit.full_page_text:
                    if len(hit.full_page_text) > truncate_page_text:
                        hit.full_page_text = hit.full_page_text[:truncate_page_text] + "..."

            # Format results with size limits
            formatted = format_search_results(enriched_hits, keyword, show_context=True)

            # Check approximate token count (rough estimate: 1 char ≈ 0.25 tokens)
            estimated_tokens = len(formatted) // 4
            if estimated_tokens > max_response_tokens:
                # Try reducing the response
                if context_padding > 0:
                    return (
                        f"⚠️ Response too large ({estimated_tokens} tokens). "
                        f"Showing limited results.\n\n" +
                        format_search_results(
                            enriched_hits[:max(1, max_pages_with_context // 2)],
                            keyword,
                            show_context=True
                        ) +
                        f"\n\n💡 **Tip**: Use context_padding=0 and lower max_pages_with_context to see more results."
                    )
                else:
                    # Already minimal, just truncate
                    return formatted[:max_response_tokens * 4] + "\n\n[Response truncated due to size limits]"

            # Add pagination info if relevant - focus on documents, not hits
            # Count unique documents in current results
            unique_docs = set()
            for hit in hits:
                unique_docs.add(hit.reference_code or hit.pid)

            # Estimate if there are more documents available
            # Since API returns more documents than requested, assume there are more if we got max_results
            if len(unique_docs) == max_results and total_hits > len(hits):
                document_start = offset // max_results * max_results + 1
                document_end = document_start + len(unique_docs) - 1
                formatted += f"\n\n📊 **Pagination**: Showing documents {document_start}-{document_end} (total {len(hits)} hits from {len(unique_docs)} documents)"
                formatted += f"\n💡 Use `offset={offset + max_results}` to see the next {max_results} documents"

            return formatted
        else:
            result = format_search_results(hits, keyword, show_context=False)

            # Add pagination info - focus on documents, not hits
            # Count unique documents in current results
            unique_docs = set()
            for hit in hits:
                unique_docs.add(hit.reference_code or hit.pid)

            # Estimate if there are more documents available
            if len(unique_docs) == max_results and total_hits > len(hits):
                document_start = offset // max_results * max_results + 1
                document_end = document_start + len(unique_docs) - 1
                result += f"\n\n📊 **Pagination**: Showing documents {document_start}-{document_end} (total {len(hits)} hits from {len(unique_docs)} documents)"
                result += f"\n💡 Use `offset={offset + max_results}` to see the next {max_results} documents"

            return result

    except Exception as e:
        return format_error(
            f"Search failed: {str(e)}",
            suggestions=[
                "Try a simpler search term",
                "Check if the service is available",
                "Reduce max_results or max_pages_with_context"
            ]
        )


@ra_mcp.tool(
    name="browse_document",
    description="Browse specific pages of a document by reference code"
)
async def browse_document(
    reference_code: str,
    pages: str,
    highlight_term: Optional[str] = None,
    max_pages: int = 20
) -> str:
    """
    Browse specific pages of a document by reference code.

    Returns:
    - Full transcribed text for each requested page
    - Optional keyword highlighting
    - Direct links to images and ALTO XML

    Examples:
    - browse_document("SE/RA/420422/01", "5") - View page 5
    - browse_document("SE/RA/420422/01", "1-10") - View pages 1 through 10
    - browse_document("SE/RA/420422/01", "5,7,9", highlight_term="Stockholm") - View specific pages with highlighting
    """
    try:
        cache = get_cache()

        # First, find the PID for this reference code
        session = HTTPClient.create_session()
        pid = None

        # Check cache for PID
        cache_params = {'reference_code': reference_code}
        pid = cache.get('structure', cache_params)

        if pid is None:
            # Try search API first
            try:
                params = {'reference_code': reference_code, 'only_digitised_materials': 'true', 'max': 1}
                response = session.get(SEARCH_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                if data.get('items'):
                    pid = data['items'][0].get('id')
                    cache.set('structure', cache_params, pid)
            except:
                pass

            # Fall back to OAI-PMH if search failed
            if not pid:
                oai_client = OAIPMHClient()
                try:
                    pid = oai_client.extract_pid(reference_code)
                    if pid:
                        cache.set('structure', cache_params, pid)
                except:
                    pass

        if not pid:
            return format_error(
                f"Could not find document with reference code '{reference_code}'",
                suggestions=[
                    "Check the reference code format",
                    "Try searching for keywords instead",
                    "The document might not be digitized"
                ]
            )

        # Get manifest information
        iiif_client = IIIFClient()
        collection_info = iiif_client.explore_collection(pid)

        manifest_id = pid
        if collection_info and collection_info.get('manifests'):
            manifest_id = collection_info['manifests'][0]['id']

        # Parse page range
        selected_pages = parse_page_range(pages)[:max_pages]

        # Load page contexts
        page_service = PageContextService()
        contexts = []

        for page_num in selected_pages:
            context = page_service.get_page_context(
                manifest_id,
                str(page_num),
                reference_code,
                highlight_term
            )
            if context:
                contexts.append(context)

        if not contexts:
            return format_error(
                f"Could not load pages for {reference_code}",
                suggestions=[
                    "The pages might not have transcriptions",
                    "Try different page numbers",
                    "Check if the document is fully digitized"
                ]
            )

        return format_page_contexts(contexts, reference_code, highlight_term)

    except Exception as e:
        return format_error(
            f"Browse failed: {str(e)}",
            suggestions=[
                "Check the reference code format",
                "Verify page numbers are valid",
                "Try with fewer pages"
            ]
        )


@ra_mcp.tool(
    name="get_document_structure",
    description="Get document structure and metadata without fetching content"
)
async def get_document_structure(
    reference_code: Optional[str] = None,
    pid: Optional[str] = None,
    include_manifest_info: bool = True
) -> str:
    """
    Get the structure and metadata of a document without fetching page content.

    Useful for:
    - Understanding what's available in a document
    - Getting the total number of pages
    - Finding available manifests
    - Viewing document hierarchy

    Provide either reference_code or pid.
    """
    try:
        if not reference_code and not pid:
            return format_error(
                "Either reference_code or pid must be provided",
                suggestions=["Provide a reference code like 'SE/RA/420422/01'", "Or provide a PID from search results"]
            )

        cache = get_cache()

        # Get PID if only reference_code provided
        if reference_code and not pid:
            session = HTTPClient.create_session()

            # Check cache
            cache_params = {'reference_code': reference_code}
            pid = cache.get('structure', cache_params)

            if pid is None:
                try:
                    params = {'reference_code': reference_code, 'only_digitised_materials': 'true', 'max': 1}
                    response = session.get(SEARCH_API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    data = response.json()
                    if data.get('items'):
                        pid = data['items'][0].get('id')
                        cache.set('structure', cache_params, pid)
                except:
                    pass

        if not pid:
            return format_error(
                f"Could not find document",
                suggestions=["Check the reference code", "Try searching for it first"]
            )

        # Clean PID if needed
        if pid.startswith('arkis!'):
            clean_pid = pid[6:]
        else:
            clean_pid = pid

        # Get IIIF collection info
        iiif_client = IIIFClient()

        # Check cache for collection info
        cache_params = {'pid': clean_pid}
        collection_info = cache.get('iiif', cache_params)

        if collection_info is None:
            collection_info = iiif_client.explore_collection(clean_pid)
            if collection_info:
                cache.set('iiif', cache_params, collection_info)

        if not collection_info:
            return format_error(
                f"Could not get structure for PID {pid}",
                suggestions=["The document might not have IIIF manifests", "Try browsing specific pages instead"]
            )

        return format_document_structure(collection_info)

    except Exception as e:
        return format_error(
            f"Failed to get document structure: {str(e)}",
            suggestions=["Check the reference code or PID", "Try searching for the document first"]
        )


@ra_mcp.resource("riksarkivet://contents/table_of_contents")
def get_table_of_contents() -> str:
    """
    Get the table of contents (Innehållsförteckning) for the Riksarkivet historical guide.

    This resource provides an overview of all available sections and topics
    covered in the historical guide to Swedish National Archives.

    Returns:
    - Complete table of contents in Swedish
    - Links to different sections and subsections
    - Hierarchical structure of the guide
    """
    try:
        # Get the path to the markdown file
        current_dir = os.path.dirname(__file__)
        markdown_path = os.path.join(current_dir, "..", "..", "markdown", "00_Innehallsforteckning.md")

        # Read the file
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content

    except FileNotFoundError:
        return format_error(
            "Table of contents file not found",
            suggestions=[
                "Check if the markdown/00_Innehallsforteckning.md file exists",
                "Verify the file path is correct"
            ]
        )
    except Exception as e:
        return format_error(
            f"Failed to load table of contents: {str(e)}",
            suggestions=["Check file permissions", "Verify file encoding is UTF-8"]
        )


@ra_mcp.tool(
    name="get_guide_content",
    description="Load specific sections from the Riksarkivet historical guide"
)
async def get_guide_content(
    filename: str = Field(description="Markdown filename to load (e.g., '01_Domstolar.md', '02_Fangelse.md')")
) -> str:
    """
    Load content from specific sections of the Riksarkivet historical guide.

    Available files include:
    - 00_Inledning.md - Introduction
    - 00_Register.md - Index
    - 01_Domstolar.md - Courts
    - 02_Fangelse.md - Prisons
    - 03_Skatt.md - Taxes
    - 04_Stadens_Forvaltning.md - City administration
    - 05_Lan.md - Counties
    - 06_Statskyrkan.md - State church
    - 07_Folkbokforing.md - Population registration
    - 08_Tull.md - Customs
    - 09_Lantmateri.md - Land surveying
    - 10_Bergsbruk.md - Mining
    - 11_Fiske.md - Fishing
    - 12_Skog.md - Forestry
    - 13_Sjukvard.md - Healthcare
    - 14_Sjofart.md - Shipping
    - 15_Vagar.md - Roads
    - 16_Tillverkning.md - Manufacturing
    - 17_Handel.md - Trade
    - 18_Lantbruk.md - Agriculture
    - 19_Skola.md - Schools
    - 20_Fattig_Socialtjanst.md - Poor relief and social services
    - 21_Kommun.md - Municipalities
    - 22_Landsting.md - County councils
    - 23_Omsorg.md - Care
    - 24_Polis.md - Police
    - 25_Invandring.md - Immigration
    - 26_Halsa_Miljo.md - Health and environment
    - 27_Djur.md - Animals
    - 28_Posten.md - Postal service
    - 29_Jarnvagen.md - Railways
    - 30_Tele.md - Telecommunications
    - 31_Byggnader.md - Buildings
    - 32_Forsorjning.md - Supply
    - 33_Barn_Ungdom.md - Children and youth
    - 34_Modrahjalp.md - Maternal aid
    - 35_Pension.md - Pensions
    - 36_Rattshjalp.md - Legal aid
    - 37_Overvakning.md - Surveillance
    - 38_Nykterhet.md - Temperance
    - 39_Arbete.md - Work
    - 40_Brand_Civilforsvar.md - Fire and civil defense
    - 41_Energi.md - Energy
    - 42_Luftfart.md - Aviation
    - 43_Kultur.md - Culture
    - 44_Internadministration.md - Internal administration
    - 45_Studiestod.md - Student aid
    - 46-61_Forsvaret.md - Defense
    - 99_Litteratur.md - Literature
    - Index.md - Index

    Parameters:
    - filename: The markdown file to load (with .md extension)

    Example:
    - get_guide_content("01_Domstolar.md") - Load courts section
    - get_guide_content("13_Sjukvard.md") - Load healthcare section
    """
    try:
        # Validate filename - ensure it ends with .md and contains no path traversal
        if not filename.endswith('.md'):
            return format_error(
                "Invalid filename format",
                suggestions=["Filename must end with .md extension"]
            )

        # Remove any path components for security
        filename = os.path.basename(filename)

        # Get the path to the markdown file
        current_dir = os.path.dirname(__file__)
        markdown_path = os.path.join(current_dir, "..", "..", "markdown", filename)

        # Check if file exists
        if not os.path.exists(markdown_path):
            return format_error(
                f"Guide section '{filename}' not found",
                suggestions=[
                    "Check the filename spelling",
                    "Use get_table_of_contents resource to see available sections",
                    "Ensure the filename includes .md extension"
                ]
            )

        # Read the file
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content

    except Exception as e:
        return format_error(
            f"Failed to load guide content '{filename}': {str(e)}",
            suggestions=[
                "Check file permissions",
                "Verify file encoding is UTF-8",
                "Ensure the filename is valid"
            ]
        )
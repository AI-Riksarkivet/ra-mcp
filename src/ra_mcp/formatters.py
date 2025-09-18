"""
Output formatters for RA-MCP server.
Converts search results and page content into well-formatted text for LLM consumption.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


def highlight_keyword(text: str, keyword: str) -> str:
    """Highlight keyword in text using markdown bold."""
    if not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"**{m.group()}**", text)


def format_search_results(hits: List[Any], keyword: str, show_context: bool = True) -> str:
    """Format search results for LLM consumption."""
    if not hits:
        return f"No results found for '{keyword}'."

    # Group hits by reference code
    grouped_hits = {}
    for hit in hits:
        ref_code = hit.reference_code or hit.pid
        if ref_code not in grouped_hits:
            grouped_hits[ref_code] = []
        grouped_hits[ref_code].append(hit)

    output = []
    output.append(f"## 🔍 Search Results: '{keyword}'")
    output.append(f"### 📊 Summary: {len(hits)} hits across {len(grouped_hits)} documents\n")

    for ref_code, ref_hits in grouped_hits.items():
        # Get metadata from first hit
        first_hit = ref_hits[0]

        output.append(f"### 📚 Document: {ref_code}")

        # Add metadata if available
        if hasattr(first_hit, 'archival_institution') and first_hit.archival_institution:
            inst = first_hit.archival_institution[0].get('caption', '') if first_hit.archival_institution else ""
            if inst:
                output.append(f"**Institution**: {inst}")

        if hasattr(first_hit, 'date') and first_hit.date:
            output.append(f"**Date**: {first_hit.date}")

        if hasattr(first_hit, 'hierarchy') and first_hit.hierarchy:
            hierarchy_path = " > ".join([h.get('caption', '') for h in first_hit.hierarchy])
            output.append(f"**Hierarchy**: {hierarchy_path}")

        output.append("")  # Blank line

        # Add page hits
        for hit in ref_hits:
            is_search_hit = hit.snippet_text != "[Context page - no search hit]"
            marker = "🎯" if is_search_hit else "📄"

            output.append(f"#### {marker} Page {hit.page_number}")

            if show_context and hasattr(hit, 'full_page_text') and hit.full_page_text:
                # Full transcription with keyword highlighting
                text = highlight_keyword(hit.full_page_text, keyword) if is_search_hit else hit.full_page_text
                output.append(text[:2000] + "..." if len(text) > 2000 else text)
            else:
                # Just snippet
                snippet = highlight_keyword(hit.snippet_text, keyword) if is_search_hit else hit.snippet_text
                output.append(f"*{snippet}*")

            output.append("")  # Blank line between pages

        output.append("---\n")  # Separator between documents

    # Add usage tips
    output.append("### 💡 Tips")
    output.append("- Use `browse_document` to view specific pages in detail")
    output.append("- Page numbers can be used directly with the browse command")
    output.append("- Reference format: `SE/RA/xxxxx/xx` identifies each document in the archives")
    output.append("- Page numbers (e.g., `00027`) refer to specific pages within each document")
    output.append("- For images and links: Use `get_document_structure` with the reference code to get IIIF manifest URLs")
    output.append("- Document reference codes can be used to access full document metadata and links")

    return "\n".join(output)


def format_page_contexts(contexts: List[Any], reference_code: str, highlight_term: Optional[str] = None) -> str:
    """Format page contexts for browsing."""
    if not contexts:
        return f"No pages found for reference code '{reference_code}'."

    output = []
    output.append(f"## 📖 Document: {reference_code}")
    output.append(f"### 📄 Displaying {len(contexts)} pages\n")

    for context in contexts:
        output.append(f"### Page {context.page_number}")

        # Full transcription with optional highlighting
        if context.full_text:
            text = highlight_keyword(context.full_text, highlight_term) if highlight_term else context.full_text
            output.append(text)
        else:
            output.append("*No transcription available for this page*")

        # Add links
        output.append("\n**Resources**:")
        output.append(f"- 📝 [ALTO XML]({context.alto_url})")
        if context.image_url:
            output.append(f"- 🖼️ [High-res Image]({context.image_url})")
        if context.bildvisning_url:
            output.append(f"- 👁️ [View in Bildvisning]({context.bildvisning_url})")

        output.append("\n---\n")  # Separator between pages

    return "\n".join(output)


def format_document_structure(structure: Dict[str, Any]) -> str:
    """Format document structure information."""
    output = []
    output.append(f"## 📚 Document Structure")

    if 'title' in structure:
        output.append(f"### {structure['title']}")

    if 'manifests' in structure:
        output.append(f"\n**Available Manifests** ({len(structure['manifests'])} total):")
        for manifest in structure['manifests'][:5]:  # Show first 5
            output.append(f"- {manifest.get('label', 'Untitled')}: {manifest.get('id', '')}")
        if len(structure['manifests']) > 5:
            output.append(f"- ... and {len(structure['manifests']) - 5} more")

    if 'collection_url' in structure:
        output.append(f"\n**Collection URL**: {structure['collection_url']}")

    return "\n".join(output)


def format_error(error_msg: str, suggestions: Optional[List[str]] = None) -> str:
    """Format error messages in a user-friendly way."""
    output = []
    output.append(f"⚠️ **Error**: {error_msg}")

    if suggestions:
        output.append("\n**Suggestions**:")
        for suggestion in suggestions:
            output.append(f"- {suggestion}")

    return "\n".join(output)
"""
Display service for formatting search results and page contexts.
Note: This is a simplified version without rich console output for MCP use.
"""

import re
from typing import List

from ..config import DEFAULT_MAX_DISPLAY
from ..models import SearchHit, PageContext


class DisplayService:
    """Service for formatting search results and page contexts."""

    @staticmethod
    def keyword_highlight(text: str, keyword: str) -> str:
        """Highlight keyword in text (simplified version for MCP)."""
        if not keyword:
            return text

        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        return pattern.sub(lambda m: f"**{m.group()}**", text)

    def format_search_hits(
        self,
        hits: List[SearchHit],
        keyword: str,
        max_display: int = DEFAULT_MAX_DISPLAY
    ) -> str:
        """Format search hits as text (simplified for MCP)."""
        if not hits:
            return "No search hits found."

        # Group hits by reference code
        grouped_hits = {}
        for hit in hits:
            ref_code = hit.reference_code or hit.pid
            if ref_code not in grouped_hits:
                grouped_hits[ref_code] = []
            grouped_hits[ref_code].append(hit)

        result_lines = []
        result_lines.append(f"Found {len(hits)} page-level hits across {len(grouped_hits)} documents")
        result_lines.append("")

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

            # Format document header
            result_lines.append(f"Document: {ref_code}")
            if institution:
                result_lines.append(f"Institution: {institution}")
            if first_hit.date:
                result_lines.append(f"Date: {first_hit.date}")

            # Format pages
            pages = sorted(set(h.page_number for h in ref_hits))
            pages_trimmed = [p.lstrip('0') or '0' for p in pages]
            result_lines.append(f"Pages with hits: {', '.join(pages_trimmed)}")

            # Add title and snippets
            title_text = first_hit.title[:100] + '...' if len(first_hit.title) > 100 else first_hit.title
            result_lines.append(f"Title: {title_text}")

            # Add snippets with page numbers
            for hit in ref_hits[:3]:  # Show max 3 snippets per reference
                snippet = hit.snippet_text[:200] + '...' if len(hit.snippet_text) > 200 else hit.snippet_text
                snippet = self.keyword_highlight(snippet, keyword)
                result_lines.append(f"  Page {hit.page_number}: {snippet}")

            if len(ref_hits) > 3:
                result_lines.append(f"  ...and {len(ref_hits) - 3} more pages with hits")

            result_lines.append("")

        return "\n".join(result_lines)

    def format_page_context(self, context: PageContext, keyword: str) -> str:
        """Format page context as text."""
        lines = []
        lines.append(f"Page {context.page_number}: {context.reference_code}")
        lines.append("")

        # Highlight keyword in text
        display_text = self.keyword_highlight(context.full_text, keyword)
        lines.append("Full Transcription:")
        lines.append(display_text)
        lines.append("")

        # Add links
        lines.append("Links:")
        lines.append(f"ALTO XML: {context.alto_url}")
        if context.image_url:
            lines.append(f"Image: {context.image_url}")
        if context.bildvisning_url:
            lines.append(f"Bildvisning: {context.bildvisning_url}")

        return "\n".join(lines)
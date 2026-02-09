"""
Plain text formatter for MCP/LLM output without any Rich markup.
"""

import re
from typing import List


class PlainTextFormatter:
    """Formatter that produces plain text without any Rich markup."""

    def format_text(self, text_content: str, style_name: str = "") -> str:
        """Return plain text without any styling."""
        return text_content

    def format_table(
        self,
        column_headers: List[str],
        table_rows: List[List[str]],
        table_title: str = "",
    ) -> str:
        """
        Create a plain text table without borders.

        Args:
            column_headers: List of column headers
            table_rows: List of row data
            table_title: Optional table title

        Returns:
            Plain text formatted table
        """
        formatted_lines = []
        if table_title:
            formatted_lines.append(table_title)
            formatted_lines.append("")

        # Calculate column widths
        all_table_rows = [column_headers] + table_rows
        column_widths = [max(len(str(row[column_index])) for row in all_table_rows) for column_index in range(len(column_headers))]

        # Format header
        formatted_header = " | ".join(column_headers[column_index].ljust(column_widths[column_index]) for column_index in range(len(column_headers)))
        formatted_lines.append(formatted_header)

        # Add simple separator
        formatted_lines.append("-" * len(formatted_header))

        # Format rows
        for data_row in table_rows:
            formatted_row = " | ".join(str(data_row[column_index]).ljust(column_widths[column_index]) for column_index in range(len(data_row)))
            formatted_lines.append(formatted_row)

        return "\n".join(formatted_lines)

    def format_panel(self, panel_content: str, panel_title: str = "", panel_border_style: str = "") -> str:
        """
        Format content as plain text without panels or borders.

        Args:
            panel_content: Content to display
            panel_title: Optional title
            panel_border_style: Ignored in plain text mode

        Returns:
            Plain text formatted content
        """
        formatted_lines = []
        if panel_title:
            formatted_lines.append(panel_title)
            formatted_lines.append("")
        formatted_lines.append(panel_content)
        return "\n".join(formatted_lines)

    def highlight_search_keyword(self, text_content: str, search_keyword: str) -> str:
        """
        Highlight search keywords using markdown-style bold.
        The **text** markers from the API are already in the correct format.
        If no markers present, fallback to manual keyword highlighting.

        Args:
            text_content: Text to search in (may already contain **text** markers)
            search_keyword: Keyword to highlight

        Returns:
            Text with keywords wrapped in **bold**
        """
        if re.search(r"\*\*[^*]+\*\*", text_content):
            return text_content

        if not search_keyword:
            return text_content
        keyword_pattern = re.compile(re.escape(search_keyword), re.IGNORECASE)
        return keyword_pattern.sub(lambda match: f"**{match.group()}**", text_content)

    def _iiif_manifest_to_bildvisaren(self, iiif_manifest_url: str) -> str:
        """
        Convert IIIF manifest URL to bildvisaren URL.

        Args:
            iiif_manifest_url: IIIF manifest URL (e.g., https://lbiiif.riksarkivet.se/arkis!R0002497/manifest)

        Returns:
            Bildvisaren URL (e.g., https://sok.riksarkivet.se/bildvisning/R0002497) or empty string if conversion fails
        """
        try:
            # Extract the ID between "arkis!" and "/manifest"
            if "arkis!" in iiif_manifest_url and "/manifest" in iiif_manifest_url:
                start_idx = iiif_manifest_url.find("arkis!") + len("arkis!")
                end_idx = iiif_manifest_url.find("/manifest", start_idx)
                manifest_id = iiif_manifest_url[start_idx:end_idx]
                return f"https://sok.riksarkivet.se/bildvisning/{manifest_id}"
            return ""
        except Exception:
            return ""

    def format_no_results_message(self, search_result) -> str:
        """
        Generate appropriate message when no results are found.

        Args:
            search_result: SearchResult containing keyword, offset, and total_hits

        Returns:
            Formatted no results message
        """
        if search_result.offset > 0:
            return f"No more results found for '{search_result.keyword}' at offset {search_result.offset}. Total results: {search_result.total_hits}"
        return f"No results found for '{search_result.keyword}'. make sure to use \"\" "

    def format_search_results(self, search_result, maximum_documents_to_display: int = 20) -> str:
        """
        Format search results as plain text with emojis for MCP/LLM consumption.

        Args:
            search_result: SearchResult containing documents and metadata
            maximum_documents_to_display: Maximum number of documents to display

        Returns:
            Formatted plain text search results
        """
        if not search_result.items:
            return self.format_no_results_message(search_result)

        lines = []
        snippet_count = search_result.count_snippets()

        # Show "100+" if we hit the max limit, indicating more are available
        document_count = len(search_result.items)
        if document_count >= search_result.max:
            document_display = f"{document_count}+"
        else:
            document_display = str(document_count)

        # Different summary for metadata search vs transcribed search
        if snippet_count > 0:
            # Transcribed text search - has page-level hits
            lines.append(f"Found {snippet_count} page-level hits across {document_display} volumes")
        else:
            # Metadata search - just document matches
            lines.append(f"Found {document_display} volumes matching metadata")
        lines.append("")

        for idx, document in enumerate(search_result.items[:maximum_documents_to_display]):
            # For transcribed search, skip documents without snippets
            # For metadata search, show all documents
            has_snippets = document.transcribed_text and document.transcribed_text.snippets
            if snippet_count > 0 and not has_snippets:
                # Transcribed search mode - skip docs without snippets
                continue

            lines.append(f"📚 Document: {document.metadata.reference_code}")

            if document.metadata.archival_institution:
                institution = document.metadata.archival_institution[0].caption
                lines.append(f"🏛️  Institution: {institution}")

            if document.metadata.date:
                lines.append(f"📅 Date: {document.metadata.date}")

            title = document.get_title()
            title_display = title[:100] + "..." if len(title) > 100 else title
            lines.append(f"📄 Title: {title_display}")

            # For metadata search, show additional contextual information
            if not has_snippets:
                # Show object type
                if document.object_type:
                    type_info = document.object_type
                    if document.type:
                        type_info += f" / {document.type}"
                    lines.append(f"🏷️  Type: {type_info}")

                # Show hierarchy (archival context)
                if document.metadata.hierarchy:
                    hierarchy_parts = [h.caption for h in document.metadata.hierarchy[:3]]
                    if hierarchy_parts:
                        hierarchy_text = " → ".join(hierarchy_parts)
                        if len(hierarchy_text) > 150:
                            hierarchy_text = hierarchy_text[:147] + "..."
                        lines.append(f"📂 Context: {hierarchy_text}")

                # Show provenance (creator/person)
                if document.metadata.provenance:
                    prov = document.metadata.provenance[0]
                    prov_text = prov.caption
                    if prov.date:
                        prov_text += f" ({prov.date})"
                    lines.append(f"👤 Creator: {prov_text}")

                # Show link to view online
                if document.links and document.links.html:
                    lines.append(f"🔗 View: {document.links.html}")

                # Show IIIF manifest if available
                if document.links and document.links.image:
                    lines.append(f"🖼️  IIIF: {document.links.image[0]}")

            # Only show pages and snippets for transcribed search (has_snippets)
            if has_snippets:
                # Extract page numbers from snippets
                page_numbers = sorted(set(page.id for snippet in document.transcribed_text.snippets for page in snippet.pages))
                # Extract just the numeric part from page IDs like "_00066" or "_H0000459_00005"
                # Split by underscore and take the last part (the actual page number)
                trimmed_page_numbers = []
                for page_id in page_numbers:
                    # Split by underscore and take last part
                    parts = page_id.split("_")
                    if parts:
                        # Get the last non-empty part and strip leading zeros
                        last_part = parts[-1]
                        trimmed = last_part.lstrip("0") or "0"
                        trimmed_page_numbers.append(trimmed)
                    else:
                        trimmed_page_numbers.append(page_id)

                doc_snippet_count = len(document.transcribed_text.snippets)
                total_hits = document.get_total_hits()
                hit_label = "hit" if doc_snippet_count == 1 else "hits"

                lines.append(f"📖 Pages with hits: {', '.join(trimmed_page_numbers)}")

                # Show total hits if available and different from shown count
                if total_hits > doc_snippet_count:
                    lines.append(f"💡 {doc_snippet_count} {hit_label} shown ({total_hits} total)")
                else:
                    lines.append(f"💡 {doc_snippet_count} {hit_label} found")

                # Show first 3 snippets
                for snippet in document.transcribed_text.snippets[:3]:
                    snippet_text = self.highlight_search_keyword(snippet.text, search_result.keyword)
                    if snippet.pages:
                        page_id = snippet.pages[0].id
                        lines.append(f"   Page {page_id}: {snippet_text}")

                if len(document.transcribed_text.snippets) > 3:
                    lines.append(f"   ...and {len(document.transcribed_text.snippets) - 3} more pages with hits")

            lines.append("")

        total_document_count = len(search_result.items)
        if total_document_count > maximum_documents_to_display:
            remaining_documents = total_document_count - maximum_documents_to_display
            lines.append(f"... and {remaining_documents} more documents")

        return "\n".join(lines)

    def format_browse_results(
        self,
        browse_result,
        highlight_term=None,
        show_links: bool = False,
        show_success_message: bool = True,
    ) -> str:
        """
        Format browse results as plain text with emojis for MCP/LLM consumption.

        Args:
            browse_result: BrowseResult containing page contexts and metadata
            highlight_term: Optional term to highlight in text
            show_links: Whether to show ALTO/Image/Bildvisning links
            show_success_message: Whether to show success message (ignored in plain text)

        Returns:
            Formatted plain text browse results
        """
        lines = []

        # Handle non-digitised materials (no pages but has metadata)
        if not browse_result.contexts and browse_result.oai_metadata:
            lines.append("⚠️ This material is not digitised or transcribed - no page images or text available.")
            lines.append("Showing metadata only:")
            lines.append("")

            metadata = browse_result.oai_metadata
            lines.append(f"📄 Reference Code: {browse_result.reference_code}")

            if metadata.title and metadata.title != "(No title)":
                lines.append(f"📋 Title: {metadata.title}")

            if metadata.unitdate:
                lines.append(f"📅 Date Range: {metadata.unitdate}")

            if metadata.repository:
                lines.append(f"🏛️  Repository: {metadata.repository}")

            if metadata.unitid and metadata.unitid != browse_result.reference_code:
                lines.append(f"🔖 Unit ID: {metadata.unitid}")

            if metadata.description:
                lines.append(f"📝 Description: {metadata.description}")

            if metadata.nad_link:
                lines.append(f"🔗 View Online: {metadata.nad_link}")

            if metadata.iiif_manifest:
                bildvisaren_url = self._iiif_manifest_to_bildvisaren(metadata.iiif_manifest)
                if bildvisaren_url:
                    lines.append(f"🖼️  View Images: {bildvisaren_url}")
                else:
                    # Fallback to IIIF manifest if conversion fails
                    lines.append(f"🖼️  IIIF Manifest: {metadata.iiif_manifest}")

            if metadata.iiif_image:
                lines.append(f"🎨 Preview Image: {metadata.iiif_image}")

            return "\n".join(lines)

        if not browse_result.contexts:
            return f"No page contexts found for {browse_result.reference_code}"

        lines.append(f"📚 Document: {browse_result.reference_code}")

        # Add OAI-PMH metadata if available
        if browse_result.oai_metadata:
            metadata = browse_result.oai_metadata

            # Display title
            if metadata.title and metadata.title != "(No title)":
                lines.append(f"📋 Title: {metadata.title}")

            # Display date range
            if metadata.unitdate:
                lines.append(f"📅 Date Range: {metadata.unitdate}")

            # Display repository
            if metadata.repository:
                lines.append(f"🏛️  Repository: {metadata.repository}")

            # Display unitid
            if metadata.unitid and metadata.unitid != browse_result.reference_code:
                lines.append(f"🔖 Unit ID: {metadata.unitid}")

            # Display description if available
            if metadata.description:
                # Truncate long descriptions for readability
                desc = metadata.description
                if len(desc) > 200:
                    desc = desc[:197] + "..."
                lines.append(f"📝 {desc}")

            # Display NAD link
            if metadata.nad_link:
                lines.append(f"🔗 NAD Link: {metadata.nad_link}")

        lines.append(f"📖 Pages loaded: {len(browse_result.contexts)}")
        lines.append("")

        for context in browse_result.contexts:
            lines.append(f"📄 Page {context.page_number}")
            lines.append("─" * 40)

            # Handle blank pages vs pages with content
            if context.full_text.strip():  # Page has text content
                display_text = context.full_text
                if highlight_term:
                    display_text = self.highlight_search_keyword(display_text, highlight_term)
                lines.append(display_text)
            else:  # Blank page
                lines.append("(Empty page - no transcribed text)")

            lines.append("")
            lines.append("🔗 Links:")
            lines.append(f"  📝 ALTO XML: {context.alto_url}")
            if context.image_url:
                lines.append(f"  🖼️  Image: {context.image_url}")
            if context.bildvisning_url:
                lines.append(f"  👁️  Bildvisning: {context.bildvisning_url}")

            lines.append("")

        return "\n".join(lines)

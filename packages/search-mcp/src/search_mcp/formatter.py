"""
Plain text formatter for MCP/LLM output without any Rich markup.
"""

import logging
import re


logger = logging.getLogger("ra_mcp.search_mcp.formatter")


def _page_id_to_number(page_id: str) -> int:
    """Extract the numeric page number from a page ID like '_00066' or '_H0000459_00005'.

    Splits by underscore and takes the last non-empty part, stripping leading zeros.
    """
    parts = page_id.split("_")
    if parts:
        last_part = parts[-1]
        trimmed = last_part.lstrip("0") or "0"
        return int(trimmed)
    return int(page_id)


class PlainTextFormatter:
    """Formatter that produces plain text without any Rich markup."""

    def format_text(self, text_content: str, style_name: str = "") -> str:
        """Return plain text without any styling."""
        return text_content

    def format_table(
        self,
        column_headers: list[str],
        table_rows: list[list[str]],
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
        all_table_rows = [column_headers, *table_rows]
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
        except Exception as e:
            logger.warning("Failed to convert IIIF manifest URL to bildvisning: %s: %s", iiif_manifest_url, e)
            return ""

    def format_error_message(self, error_message: str, error_suggestions: list[str] | None = None) -> str:
        """
        Format an error message with optional suggestions.

        Args:
            error_message: The error message to display
            error_suggestions: Optional list of suggestion strings

        Returns:
            Formatted error message with suggestions
        """
        formatted_lines = [f"⚠️ **Error**: {error_message}"]
        if error_suggestions:
            formatted_lines.append("\n**Suggestions**:")
            formatted_lines.extend(f"- {suggestion_text}" for suggestion_text in error_suggestions)
        return "\n".join(formatted_lines)

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

    def _format_document_header(self, lines: list[str], document) -> None:
        """Emit ref_code, institution, date, and title lines for a document."""
        lines.append(f"📚 Document: {document.metadata.reference_code}")

        if document.metadata.archival_institution:
            institution = document.metadata.archival_institution[0].caption
            lines.append(f"🏛️  Institution: {institution}")

        if document.metadata.date:
            lines.append(f"📅 Date: {document.metadata.date}")

        title = document.get_title()
        title_display = title[:100] + "..." if len(title) > 100 else title
        lines.append(f"📄 Title: {title_display}")

    def _format_metadata_fields(self, lines: list[str], document) -> None:
        """Emit type, hierarchy, provenance, link, and IIIF lines for metadata-only documents."""
        if document.object_type:
            type_info = document.object_type
            if document.type:
                type_info += f" / {document.type}"
            lines.append(f"🏷️  Type: {type_info}")

        if document.metadata.hierarchy:
            hierarchy_parts = [h.caption for h in document.metadata.hierarchy[:3]]
            if hierarchy_parts:
                hierarchy_text = " → ".join(hierarchy_parts)
                if len(hierarchy_text) > 150:
                    hierarchy_text = hierarchy_text[:147] + "..."
                lines.append(f"📂 Context: {hierarchy_text}")

        if document.metadata.provenance:
            prov = document.metadata.provenance[0]
            prov_text = prov.caption
            if prov.date:
                prov_text += f" ({prov.date})"
            lines.append(f"👤 Creator: {prov_text}")

        if document.links and document.links.html:
            lines.append(f"🔗 View: {document.links.html}")

        if document.links and document.links.image:
            bildvisaren_url = self._iiif_manifest_to_bildvisaren(document.links.image[0])
            if bildvisaren_url:
                lines.append(f"🖼️  View Images: {bildvisaren_url}")
            else:
                lines.append(f"🖼️  IIIF: {document.links.image[0]}")

    def _format_document_snippets(self, lines: list[str], document, keyword: str) -> None:
        """Emit page numbers, hit counts, and first 3 snippets for a transcribed document."""
        page_numbers = sorted({page.id for snippet in document.transcribed_text.snippets for page in snippet.pages})
        trimmed_page_numbers = [str(_page_id_to_number(pid)) for pid in page_numbers]

        doc_snippet_count = len(document.transcribed_text.snippets)
        total_hits = document.get_total_hits()
        hit_label = "hit" if doc_snippet_count == 1 else "hits"

        lines.append(f"📖 Pages with hits: {', '.join(trimmed_page_numbers)}")

        if total_hits > doc_snippet_count:
            lines.append(f"💡 {doc_snippet_count} {hit_label} shown ({total_hits} total)")
        else:
            lines.append(f"💡 {doc_snippet_count} {hit_label} found")

        for snippet in document.transcribed_text.snippets[:3]:
            snippet_text = self.highlight_search_keyword(snippet.text, keyword)
            if snippet.pages:
                page_id = snippet.pages[0].id
                lines.append(f"   Page {page_id}: {snippet_text}")

        if len(document.transcribed_text.snippets) > 3:
            lines.append(f"   ...and {len(document.transcribed_text.snippets) - 3} more pages with hits")

    def format_search_results(
        self,
        search_result,
        maximum_documents_to_display: int = 20,
        seen_pages: dict[str, list[int]] | None = None,
    ) -> str:
        """
        Format search results as plain text with emojis for MCP/LLM consumption.

        Args:
            search_result: SearchResult containing documents and metadata
            maximum_documents_to_display: Maximum number of documents to display
            seen_pages: Optional dict mapping reference_code to list of already-seen page numbers.
                        When provided, documents/snippets that were already shown are compacted or skipped.

        Returns:
            Formatted plain text search results
        """
        if not search_result.items:
            self.items_scanned = 0
            return self.format_no_results_message(search_result)

        lines = []
        snippet_count = search_result.count_snippets()
        skipped_count = 0
        displayed_count = 0
        items_scanned = 0

        # Show "100+" if we hit the max limit, indicating more are available
        document_count = len(search_result.items)
        if document_count >= search_result.max:
            document_display = f"{document_count}+"
        else:
            document_display = str(document_count)

        # Different summary for metadata search vs transcribed search
        if snippet_count > 0:
            lines.append(f"Found {snippet_count} page-level hits across {document_display} volumes")
        else:
            lines.append(f"Found {document_display} volumes matching metadata")
        lines.append("")

        # Iterate all items — skipped (deduped) docs don't count against the display limit
        for idx, document in enumerate(search_result.items):
            if displayed_count >= maximum_documents_to_display:
                break
            items_scanned = idx + 1

            has_snippets = document.transcribed_text and document.transcribed_text.snippets
            if snippet_count > 0 and not has_snippets:
                continue

            ref_code = document.metadata.reference_code

            # --- Dedup logic ---
            if seen_pages is not None and ref_code in seen_pages:
                prev_page_nums = set(seen_pages.get(ref_code, []))

                if has_snippets:
                    new_snippets = [s for s in document.transcribed_text.snippets if any(_page_id_to_number(p.id) not in prev_page_nums for p in s.pages)]
                    if not new_snippets:
                        skipped_count += 1
                        continue
                    lines.append(f"📚 Document: {ref_code} (previously shown — new pages only)")
                    self._format_compact_snippets(lines, new_snippets, search_result.keyword)
                    lines.append("")
                    displayed_count += 1
                    continue
                skipped_count += 1
                continue

            # --- Full rendering ---
            displayed_count += 1
            self._format_document_header(lines, document)

            if not has_snippets:
                self._format_metadata_fields(lines, document)

            if has_snippets:
                self._format_document_snippets(lines, document, search_result.keyword)

            lines.append("")

        if skipped_count > 0:
            lines.append(f"({skipped_count} previously shown document(s) omitted)")
            lines.append("")

        # Track how many items were scanned so the caller can limit state updates
        self.items_scanned = items_scanned

        total_remaining = len(search_result.items) - items_scanned
        if total_remaining > 0:
            lines.append(f"... and {total_remaining} more documents")

        return "\n".join(lines)

    def _format_compact_snippets(self, lines: list[str], snippets: list, keyword: str) -> None:
        """Render snippets compactly for a previously-seen document (new pages only)."""
        page_numbers = sorted({page.id for snippet in snippets for page in snippet.pages})
        trimmed = [str(_page_id_to_number(pid)) for pid in page_numbers]
        lines.append(f"📖 New pages: {', '.join(trimmed)}")
        for snippet in snippets[:3]:
            snippet_text = self.highlight_search_keyword(snippet.text, keyword)
            if snippet.pages:
                page_id = snippet.pages[0].id
                lines.append(f"   Page {page_id}: {snippet_text}")
        if len(snippets) > 3:
            lines.append(f"   ...and {len(snippets) - 3} more pages with hits")

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
        if not browse_result.contexts:
            return f"No page contexts found for {browse_result.reference_code}"

        lines = []
        lines.append(f"📚 Document: {browse_result.reference_code}")

        # Add OAI-PMH metadata if available
        if browse_result.oai_metadata:
            metadata = browse_result.oai_metadata

            # Display title
            if metadata.title and metadata.title != "(No title)":
                lines.append(f"📋 Title: {metadata.title}")

            # Display repository
            if metadata.repository:
                lines.append(f"🏛️  Repository: {metadata.repository}")

            # Display unitid
            if metadata.unitid and metadata.unitid != browse_result.reference_code:
                lines.append(f"🔖 Unit ID: {metadata.unitid}")

            # Display NAD link
            if metadata.nad_link:
                lines.append(f"🔗 NAD Link: {metadata.nad_link}")

        lines.append(f"📖 Pages loaded: {len(browse_result.contexts)}")
        lines.append("")

        for context in browse_result.contexts:
            lines.append(f"📄 Page {context.page_number}")
            lines.append("─" * 40)

            display_text = context.full_text
            if highlight_term:
                display_text = self.highlight_search_keyword(display_text, highlight_term)

            lines.append(display_text)
            lines.append("")
            lines.append("🔗 Links:")
            lines.append(f"  📝 ALTO XML: {context.alto_url}")
            if context.image_url:
                lines.append(f"  🖼️  Image: {context.image_url}")
            if context.bildvisning_url:
                lines.append(f"  👁️  Bildvisning: {context.bildvisning_url}")

            lines.append("")

        return "\n".join(lines)

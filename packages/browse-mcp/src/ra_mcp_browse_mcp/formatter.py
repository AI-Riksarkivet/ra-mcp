"""
Plain text formatter for MCP/LLM output without any Rich markup.
"""

from ra_mcp_common.utils.formatting import highlight_keyword_markdown, iiif_manifest_to_bildvisaren, page_id_to_number


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
        """Highlight search keywords using markdown-style bold."""
        return highlight_keyword_markdown(text_content, search_keyword)

    def _iiif_manifest_to_bildvisaren(self, iiif_manifest_url: str) -> str:
        """Convert IIIF manifest URL to bildvisaren URL."""
        return iiif_manifest_to_bildvisaren(iiif_manifest_url)

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
            lines.append(f"🖼️  IIIF: {document.links.image[0]}")

    def _format_document_snippets(self, lines: list[str], document, keyword: str) -> None:
        """Emit page numbers, hit counts, and first 3 snippets for a transcribed document."""
        page_numbers = sorted({page.id for snippet in document.transcribed_text.snippets for page in snippet.pages})
        trimmed_page_numbers = [str(page_id_to_number(pid)) for pid in page_numbers]

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
        if document_count >= search_result.limit:
            document_display = f"{document_count}+"
        else:
            document_display = str(document_count)

        if snippet_count > 0:
            lines.append(f"Found {snippet_count} page-level hits across {document_display} volumes")
        else:
            lines.append(f"Found {document_display} volumes matching metadata")
        lines.append("")

        for _idx, document in enumerate(search_result.items[:maximum_documents_to_display]):
            has_snippets = document.transcribed_text and document.transcribed_text.snippets
            if snippet_count > 0 and not has_snippets:
                continue

            self._format_document_header(lines, document)

            if not has_snippets:
                self._format_metadata_fields(lines, document)

            if has_snippets:
                self._format_document_snippets(lines, document, search_result.keyword)

            lines.append("")

        total_document_count = len(search_result.items)
        if total_document_count > maximum_documents_to_display:
            remaining_documents = total_document_count - maximum_documents_to_display
            lines.append(f"... and {remaining_documents} more documents")

        return "\n".join(lines)

    def _format_non_digitised_metadata(self, lines: list[str], browse_result) -> bool:
        """Format metadata for non-digitised materials. Returns True if handled (early return)."""
        if browse_result.contexts or not browse_result.oai_metadata:
            return False

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
                lines.append(f"🖼️  IIIF Manifest: {metadata.iiif_manifest}")

        if metadata.iiif_image:
            lines.append(f"🎨 Preview Image: {metadata.iiif_image}")

        return True

    def _format_oai_metadata(self, lines: list[str], metadata, ref_code: str) -> None:
        """Format OAI-PMH metadata section for a digitised document."""
        if metadata.title and metadata.title != "(No title)":
            lines.append(f"📋 Title: {metadata.title}")

        if metadata.unitdate:
            lines.append(f"📅 Date Range: {metadata.unitdate}")

        if metadata.repository:
            lines.append(f"🏛️  Repository: {metadata.repository}")

        if metadata.unitid and metadata.unitid != ref_code:
            lines.append(f"🔖 Unit ID: {metadata.unitid}")

        if metadata.description:
            desc = metadata.description
            if len(desc) > 200:
                desc = desc[:197] + "..."
            lines.append(f"📝 {desc}")

        if metadata.nad_link:
            lines.append(f"🔗 NAD Link: {metadata.nad_link}")

    def format_browse_results(
        self,
        browse_result,
        highlight_term=None,
        show_links: bool = False,
        show_success_message: bool = True,
        seen_page_numbers: set[int] | None = None,
    ) -> str:
        """
        Format browse results as plain text with emojis for MCP/LLM consumption.

        Args:
            browse_result: BrowseResult containing page contexts and metadata
            highlight_term: Optional term to highlight in text
            show_links: Whether to show ALTO/Image/Bildvisning links
            show_success_message: Whether to show success message (ignored in plain text)
            seen_page_numbers: Optional set of page numbers already shown in this session.
                               When provided, previously-shown pages get a one-liner stub.

        Returns:
            Formatted plain text browse results
        """
        lines: list[str] = []

        if self._format_non_digitised_metadata(lines, browse_result):
            return "\n".join(lines)

        if not browse_result.contexts:
            return f"No page contexts found for {browse_result.reference_code}"

        seen = seen_page_numbers or set()

        lines.append(f"📚 Document: {browse_result.reference_code}")

        if browse_result.oai_metadata:
            self._format_oai_metadata(lines, browse_result.oai_metadata, browse_result.reference_code)

        # Summary line with dedup info
        new_count = sum(1 for c in browse_result.contexts if c.page_number not in seen)
        reseen_count = len(browse_result.contexts) - new_count
        if seen and reseen_count > 0:
            lines.append(f"📖 Pages loaded: {len(browse_result.contexts)} ({new_count} new, {reseen_count} previously shown)")
        else:
            lines.append(f"📖 Pages loaded: {len(browse_result.contexts)}")
        lines.append("")

        for context in browse_result.contexts:
            if context.page_number in seen:
                lines.append(f"📄 Page {context.page_number} (previously shown in this session)")
                lines.append("")
                continue

            lines.append(f"📄 Page {context.page_number}")
            lines.append("─" * 40)

            if context.full_text.strip():
                display_text = context.full_text
                if highlight_term:
                    display_text = self.highlight_search_keyword(display_text, highlight_term)
                lines.append(display_text)
            else:
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

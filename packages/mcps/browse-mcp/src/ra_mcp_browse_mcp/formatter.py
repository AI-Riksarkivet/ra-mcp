"""
Plain text formatter for MCP/LLM output without any Rich markup.
"""

from ra_mcp_common.formatting import highlight_keyword_markdown, iiif_manifest_to_bildvisaren


class PlainTextFormatter:
    """Formatter that produces plain text without any Rich markup."""

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

    def _format_non_digitised_metadata(self, lines: list[str], browse_result) -> bool:
        """Format metadata for non-digitised materials. Returns True if handled (early return)."""
        if browse_result.contexts or not browse_result.oai_metadata:
            return False

        # A manifest means the material IS digitised — empty contexts then mean the
        # requested page(s) don't exist / the range is inverted, not "not digitised".
        if browse_result.manifest_id:
            lines.append(f"⚠️ No pages found for the requested page(s) '{browse_result.pages_requested}'.")
            lines.append("This material IS digitised — check the page number(s) exist and that any range is not inverted (use e.g. 1-10, not 10-1).")
        else:
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
        seen_page_numbers: set[int] | None = None,
    ) -> str:
        """
        Format browse results as plain text with emojis for MCP/LLM consumption.

        Args:
            browse_result: BrowseResult containing page contexts and metadata
            highlight_term: Optional term to highlight in text
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

        lines.append(
            "Tip: Present the original text (quoted), provide a translation in the user's language, and include the bildvisaren link. Note uncertain readings."
        )

        return "\n".join(lines)

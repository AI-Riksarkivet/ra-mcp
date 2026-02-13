"""
Shared formatting utilities for MCP tool output.

These functions are used by both search-mcp and browse-mcp formatters
to produce plain-text/markdown output suitable for LLM consumption.
"""

import logging
import re


logger = logging.getLogger("ra_mcp.formatting")


def format_error_message(error_message: str, error_suggestions: list[str] | None = None) -> str:
    """Format an error message with optional suggestions."""
    formatted_lines = [f"\u26a0\ufe0f **Error**: {error_message}"]
    if error_suggestions:
        formatted_lines.append("\n**Suggestions**:")
        formatted_lines.extend(f"- {suggestion_text}" for suggestion_text in error_suggestions)
    return "\n".join(formatted_lines)


def page_id_to_number(page_id: str) -> int:
    """Extract the numeric page number from a page ID like '_00066' or '_H0000459_00005'.

    Splits by underscore and takes the last non-empty part, stripping leading zeros.
    """
    parts = page_id.split("_")
    if parts:
        last_part = parts[-1]
        trimmed = last_part.lstrip("0") or "0"
        return int(trimmed)
    return int(page_id)


def iiif_manifest_to_bildvisaren(iiif_manifest_url: str) -> str:
    """Convert IIIF manifest URL to bildvisaren URL.

    Args:
        iiif_manifest_url: IIIF manifest URL (e.g., https://lbiiif.riksarkivet.se/arkis!R0002497/manifest)

    Returns:
        Bildvisaren URL (e.g., https://sok.riksarkivet.se/bildvisning/R0002497) or empty string if conversion fails
    """
    try:
        if "arkis!" in iiif_manifest_url and "/manifest" in iiif_manifest_url:
            start_idx = iiif_manifest_url.find("arkis!") + len("arkis!")
            end_idx = iiif_manifest_url.find("/manifest", start_idx)
            manifest_id = iiif_manifest_url[start_idx:end_idx]
            return f"https://sok.riksarkivet.se/bildvisning/{manifest_id}"
        return ""
    except Exception as e:
        logger.warning("Failed to convert IIIF manifest URL to bildvisning: %s: %s", iiif_manifest_url, e)
        return ""


def highlight_keyword_markdown(text_content: str, search_keyword: str) -> str:
    """Highlight search keywords using markdown-style bold.

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

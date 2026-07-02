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


def trim_page_number(page_number: str) -> str:
    """Remove leading underscores and zeros from page number, keeping at least one digit."""
    return page_number.lstrip("_0") or "0"


def trim_page_numbers(page_numbers: list[str]) -> list[str]:
    """Remove leading zeros from multiple page numbers."""
    return [trim_page_number(p) for p in page_numbers]


def truncate_text(text: str, max_length: int, add_ellipsis: bool = True) -> str:
    """Truncate text to maximum length, optionally adding ellipsis."""
    if len(text) <= max_length:
        return text

    if add_ellipsis and max_length > 3:
        return text[: max_length - 3] + "..."
    return text[:max_length]


def format_example_browse_command(reference_code: str, page_numbers: list[str], search_term: str = "") -> str:
    """Format an example browse command for display."""
    if len(page_numbers) == 0:
        return ""

    if len(page_numbers) == 1:
        cmd = f'ra browse "{reference_code}" --page {page_numbers[0]}'
    else:
        pages_str = ",".join(page_numbers[:5])  # Show max 5 pages
        cmd = f'ra browse "{reference_code}" --page "{pages_str}"'

    if search_term:
        cmd += f' --search-term "{search_term}"'

    return cmd


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

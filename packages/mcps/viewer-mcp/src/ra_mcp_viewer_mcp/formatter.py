"""Output formatting for viewer tool results."""

from fastmcp.tools import ToolResult
from mcp import types


def error_result(msg: str) -> ToolResult:
    """Build a text-only error result."""
    return ToolResult(content=[types.TextContent(type="text", text=msg)])


def text_result(msg: str) -> ToolResult:
    """Build a text-only success result."""
    return ToolResult(content=[types.TextContent(type="text", text=msg)])


def build_summary(
    page_count: int,
    page_numbers: list[int],
    has_ui: bool,
    image_urls: list[str],
    reference_code: str = "",
) -> str:
    """Build a lean initial summary for the LLM.

    When the viewer UI is active, updateModelContext provides live page
    transcription, selection, and search state — so we keep this minimal.
    When there is no UI, we include image URLs as fallback.
    """
    label = f"{page_count} page(s)" + (f" of {reference_code}" if reference_code else "")
    pages_str = _format_page_range(page_numbers)
    parts = [f"Opened viewer: {label}, {pages_str}."]
    if has_ui:
        parts.append("The viewer will send live context (page text, selection, search) via updateModelContext.")
    else:
        parts.append("Image URLs:\n" + "\n".join(image_urls))
    return "\n".join(parts)


def _format_page_range(page_numbers: list[int]) -> str:
    """Format page numbers concisely: [7,8,9,11] → 'pages 7-9, 11'."""
    if not page_numbers:
        return "no pages"
    if len(page_numbers) == 1:
        return f"page {page_numbers[0]}"

    ranges: list[str] = []
    start = page_numbers[0]
    prev = start
    for n in page_numbers[1:]:
        if n == prev + 1:
            prev = n
        else:
            ranges.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = n
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return f"pages {', '.join(ranges)}"

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
    transcription: str,
    page_number: int,
    has_ui: bool,
    image_urls: list[str],
    reference_code: str = "",
) -> str:
    """Build the text content summary for the LLM."""
    label = f"{page_count} page(s)" + (f" of {reference_code}" if reference_code else "")
    parts = [f"Displaying {label}."]
    if transcription:
        parts.append(f"Page {page_number} transcription:")
        parts.append(transcription)
    else:
        parts.append(f"Page {page_number}: (no transcribed text)")
    if not has_ui:
        parts.append("\nImage URLs:\n" + "\n".join(image_urls))
    return "\n".join(parts)

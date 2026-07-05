"""Plain-text formatters for Rosenberg search results."""

from __future__ import annotations

from ra_mcp_dataset_lib import format_results
from ra_mcp_rosenberg_lib.search_operations import SearchResult


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len characters, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _append_if(lines: list[str], label: str, value: str) -> None:
    """Append 'Label: value' to lines if value is truthy."""
    if value:
        lines.append(f"{label}: {value}")


def _format_rosenberg_record(rec: dict, lines: list[str]) -> None:
    """Format a single Rosenberg record into lines."""
    lines.append(f"--- Rosenberg {rec.get('post_id', '?')} ---")
    _append_if(lines, "Place", rec.get("plats", ""))
    _append_if(lines, "Parish", rec.get("forsamling", ""))

    harad = rec.get("harad", "")
    tingslag = rec.get("tingslag", "")
    if harad or tingslag:
        parts = [p for p in [harad, tingslag] if p]
        lines.append(f"Hundred: {' / '.join(parts)}")

    _append_if(lines, "County", rec.get("lan", ""))

    beskrivning = rec.get("beskrivning", "")
    if beskrivning:
        lines.append(f"Description: {_truncate(beskrivning, 300)}")

    # Collect industries with "1"
    from ra_mcp_rosenberg_lib.models import _INDUSTRY_DISPLAY

    industry_names = []
    for field_name, display_name in _INDUSTRY_DISPLAY.items():
        if rec.get(field_name) == "1":
            industry_names.append(display_name)
    if industry_names:
        lines.append(f"Industries: {', '.join(industry_names)}")

    lines.append("")


def format_rosenberg_results(result: SearchResult) -> str:
    """Format Rosenberg search results as plain text for MCP/LLM consumption."""
    return format_results(result, label="Rosenberg", render_record=_format_rosenberg_record)

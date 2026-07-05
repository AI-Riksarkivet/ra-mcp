"""Plain-text formatters for Filmcensur search results."""

from __future__ import annotations

from ra_mcp_dataset_lib import format_results
from ra_mcp_filmcensur_lib.search_operations import SearchResult


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len characters, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _append_if(lines: list[str], label: str, value: str) -> None:
    """Append 'Label: value' to lines if value is truthy."""
    if value:
        lines.append(f"{label}: {value}")


def _format_filmreg_record(rec: dict, lines: list[str]) -> None:
    """Format a single Filmreg record into lines."""
    lines.append(f"--- Film {rec.get('granskningsnummer', '?')} ---")
    _append_if(lines, "Title", rec.get("titel_org", ""))
    _append_if(lines, "Swedish title", rec.get("titel_svensk", ""))
    _append_if(lines, "Year", rec.get("produktionsaar", ""))

    kategori = rec.get("filmkategori", "")
    filmtyp = rec.get("filmtyp", "")
    if kategori or filmtyp:
        cat_parts = [p for p in [kategori, filmtyp] if p]
        lines.append(f"Category: {' / '.join(cat_parts)}")

    _append_if(lines, "Country", rec.get("produktionsland", ""))
    _append_if(lines, "Producer", rec.get("producent", ""))
    _append_if(lines, "Age rating", rec.get("aaldersgraens", ""))
    _append_if(lines, "Cuts", rec.get("klipp_antal", ""))
    _append_if(lines, "Duration", rec.get("beslut_laengd", ""))
    _append_if(lines, "Decision", rec.get("beslutsdatum", ""))

    fri_text = rec.get("fri_text", "")
    if fri_text:
        lines.append(f"Description: {_truncate(fri_text, 200)}")

    lines.append("")


def format_filmreg_results(result: SearchResult) -> str:
    """Format Filmreg search results as plain text for MCP/LLM consumption."""
    return format_results(result, label="Filmreg", render_record=_format_filmreg_record)

"""Plain-text formatters for Filmcensur search results."""

from __future__ import annotations

from typing import Any

from ra_mcp_common.formatting import append_if, truncate_text
from ra_mcp_dataset_lib import format_results
from ra_mcp_filmcensur_lib.search_operations import SearchResult


def _format_filmreg_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Filmreg record into lines."""
    lines.append(f"--- Film {rec.get('granskningsnummer', '?')} ---")
    append_if(lines, "Title", rec.get("titel_org", ""))
    append_if(lines, "Swedish title", rec.get("titel_svensk", ""))
    append_if(lines, "Year", rec.get("produktionsaar", ""))

    kategori = rec.get("filmkategori", "")
    filmtyp = rec.get("filmtyp", "")
    if kategori or filmtyp:
        cat_parts = [p for p in [kategori, filmtyp] if p]
        lines.append(f"Category: {' / '.join(cat_parts)}")

    append_if(lines, "Country", rec.get("produktionsland", ""))
    append_if(lines, "Producer", rec.get("producent", ""))
    append_if(lines, "Age rating", rec.get("aaldersgraens", ""))
    append_if(lines, "Cuts", rec.get("klipp_antal", ""))
    append_if(lines, "Duration", rec.get("beslut_laengd", ""))
    append_if(lines, "Decision", rec.get("beslutsdatum", ""))

    fri_text = rec.get("fri_text", "")
    if fri_text:
        lines.append(f"Description: {truncate_text(fri_text, 200)}")

    lines.append("")


def format_filmreg_results(result: SearchResult) -> str:
    """Format Filmreg search results as plain text for MCP/LLM consumption."""
    return format_results(result, label="Filmreg", render_record=_format_filmreg_record)

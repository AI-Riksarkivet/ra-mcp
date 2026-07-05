"""Plain-text formatters for SJ railway records search results."""

from __future__ import annotations

from typing import Any

from ra_mcp_common.formatting import append_if, truncate_text
from ra_mcp_dataset_lib import format_results
from ra_mcp_sj_lib.search_operations import SearchResult


# ---------------------------------------------------------------------------
# JUDA formatter
# ---------------------------------------------------------------------------


def _format_juda_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single JUDA property record into lines."""
    lines.append(f"--- JUDA {rec.get('fbidnr', '?')} ---")
    append_if(lines, "Property", rec.get("fbtext", ""))
    append_if(lines, "County", rec.get("fblan", ""))
    append_if(lines, "Municipality", rec.get("fbkom", ""))
    append_if(lines, "Owner", rec.get("fbagrkod2", ""))

    fbanm = rec.get("fbanm", "")
    if fbanm:
        lines.append(f"Notes: {truncate_text(fbanm, 150)}")

    lines.append("")


def format_juda_results(result: SearchResult) -> str:
    """Format JUDA search results as plain text for MCP/LLM consumption."""
    return format_results(result, label="JUDA", render_record=_format_juda_record)


# ---------------------------------------------------------------------------
# Ritningar formatter
# ---------------------------------------------------------------------------


def _format_ritning_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single drawing record into lines."""
    bnum = rec.get("bnum", "?")
    blad = rec.get("blad", "")
    header = f"--- Ritning {bnum}/{blad} ---" if blad else f"--- Ritning {bnum} ---"
    lines.append(header)
    append_if(lines, "Station", rec.get("ben1", ""))
    append_if(lines, "Description", rec.get("ben", ""))
    append_if(lines, "Drawing", rec.get("ritn", ""))
    append_if(lines, "Date", rec.get("datm", ""))
    append_if(lines, "Format", rec.get("form2", ""))
    append_if(lines, "Type", rec.get("rtyp2", ""))
    append_if(lines, "District", rec.get("dkod", ""))
    append_if(lines, "Building type", rec.get("sakg", ""))
    lines.append("")


def format_ritningar_results(result: SearchResult) -> str:
    """Format drawing search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more drawing results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No drawing results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Drawing search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_ritning_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)

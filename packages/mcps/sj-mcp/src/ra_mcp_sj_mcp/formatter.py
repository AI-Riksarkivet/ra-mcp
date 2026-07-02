"""Plain-text formatters for SJ railway records search results."""

from __future__ import annotations

from ra_mcp_sj_lib.search_operations import SearchResult


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len characters, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _append_if(lines: list[str], label: str, value: str) -> None:
    """Append 'Label: value' to lines if value is truthy."""
    if value:
        lines.append(f"{label}: {value}")


# ---------------------------------------------------------------------------
# JUDA formatter
# ---------------------------------------------------------------------------


def _format_juda_record(rec: dict, lines: list[str]) -> None:
    """Format a single JUDA property record into lines."""
    lines.append(f"--- JUDA {rec.get('fbidnr', '?')} ---")
    _append_if(lines, "Property", rec.get("fbtext", ""))
    _append_if(lines, "County", rec.get("fblan", ""))
    _append_if(lines, "Municipality", rec.get("fbkom", ""))
    _append_if(lines, "Owner", rec.get("fbagrkod2", ""))

    fbanm = rec.get("fbanm", "")
    if fbanm:
        lines.append(f"Notes: {_truncate(fbanm, 150)}")

    lines.append("")


def format_juda_results(result: SearchResult) -> str:
    """Format JUDA search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more JUDA results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No JUDA results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"JUDA search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_juda_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Ritningar formatter
# ---------------------------------------------------------------------------


def _format_ritning_record(rec: dict, lines: list[str]) -> None:
    """Format a single drawing record into lines."""
    bnum = rec.get("bnum", "?")
    blad = rec.get("blad", "")
    header = f"--- Ritning {bnum}/{blad} ---" if blad else f"--- Ritning {bnum} ---"
    lines.append(header)
    _append_if(lines, "Station", rec.get("ben1", ""))
    _append_if(lines, "Description", rec.get("ben", ""))
    _append_if(lines, "Drawing", rec.get("ritn", ""))
    _append_if(lines, "Date", rec.get("datm", ""))
    _append_if(lines, "Format", rec.get("form2", ""))
    _append_if(lines, "Type", rec.get("rtyp2", ""))
    _append_if(lines, "District", rec.get("dkod", ""))
    _append_if(lines, "Building type", rec.get("sakg", ""))
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

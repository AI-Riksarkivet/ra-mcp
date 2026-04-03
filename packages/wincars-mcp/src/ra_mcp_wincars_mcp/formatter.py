"""Plain-text formatters for Wincars search results."""

from __future__ import annotations

from ra_mcp_wincars_lib.models import _TYP_DISPLAY
from ra_mcp_wincars_lib.search_operations import SearchResult


_STATUS_DISPLAY: dict[str, str] = {
    "A": "Avregistrerad (written off)",
    "S": "Skrotad (scrapped)",
}


def _append_if(lines: list[str], label: str, value: str) -> None:
    """Append 'Label: value' to lines if value is truthy."""
    if value:
        lines.append(f"{label}: {value}")


def _format_wincars_record(rec: dict, lines: list[str]) -> None:
    """Format a single Wincars record into lines."""
    nreg = rec.get("nreg", "?")
    lines.append(f"--- {nreg} ---")

    typ_code = rec.get("typ", "")
    typ_name = _TYP_DISPLAY.get(typ_code, typ_code)
    if typ_code:
        lines.append(f"Type: {typ_name} ({typ_code})")

    _append_if(lines, "Make", rec.get("fabrikat", ""))
    _append_if(lines, "Year", rec.get("aar", ""))

    mreg = rec.get("mreg", "")
    freg = rec.get("freg", "")
    if mreg or freg:
        parts = []
        if mreg:
            parts.append(mreg)
        if freg:
            parts.append(f"prev: {freg}")
        lines.append(f"Reg: {', '.join(parts)}")

    _append_if(lines, "Chassis", rec.get("cnr", ""))
    _append_if(lines, "Engine", rec.get("mnr", ""))
    _append_if(lines, "Domicile", rec.get("hemvist", ""))
    _append_if(lines, "Registered", rec.get("antag", ""))
    _append_if(lines, "Deregistered", rec.get("avreg", ""))

    status_code = rec.get("status", "")
    status_display = _STATUS_DISPLAY.get(status_code, "")
    if status_display:
        lines.append(f"Status: {status_display}")

    _append_if(lines, "Notes", rec.get("anm", ""))

    lines.append("")


def format_wincars_results(result: SearchResult) -> str:
    """Format Wincars search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more Wincars results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No Wincars results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Wincars search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_wincars_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)

"""Plain-text formatters for Fältjägare search results."""

from __future__ import annotations

from ra_mcp_faltjagare_lib.search_operations import SearchResult


def _append_if(lines: list[str], label: str, value: str) -> None:
    """Append 'Label: value' to lines if value is truthy."""
    if value:
        lines.append(f"{label}: {value}")


def _format_faltjagare_record(rec: dict, lines: list[str]) -> None:
    """Format a single Fältjägare record into lines."""
    soldatnamn = rec.get("soldatnamn", "")
    foernamn = rec.get("foernamn", "")
    familjenamn = rec.get("familjenamn", "")

    name_parts = [p for p in [foernamn, familjenamn] if p]
    name_extra = f" ({' '.join(name_parts)})" if name_parts else ""
    lines.append(f"--- {soldatnamn}{name_extra} ---")

    _append_if(lines, "Rank", rec.get("befattning", ""))
    _append_if(lines, "Company", rec.get("kompani", ""))

    rotens_socken = rec.get("rotens_socken", "")
    region = rec.get("region", "")
    if rotens_socken and region:
        lines.append(f"Parish: {rotens_socken}, {region}")
    elif rotens_socken:
        lines.append(f"Parish: {rotens_socken}")
    elif region:
        lines.append(f"Region: {region}")

    from_tjaenst = rec.get("from_tjaenst", "")
    till_tjaenst = rec.get("till_tjaenst", "")
    if from_tjaenst or till_tjaenst:
        lines.append(f"Service: {from_tjaenst} - {till_tjaenst}")

    foedelsedatum = rec.get("foedelsedatum", "")
    foedelsesocken = rec.get("foedelsesocken", "")
    if foedelsedatum and foedelsesocken:
        lines.append(f"Born: {foedelsedatum}, {foedelsesocken}")
    elif foedelsedatum:
        lines.append(f"Born: {foedelsedatum}")
    elif foedelsesocken:
        lines.append(f"Born: {foedelsesocken}")

    doedsdatum = rec.get("doedsdatum", "")
    doedsort = rec.get("doedsort", "")
    if doedsdatum and doedsort:
        lines.append(f"Died: {doedsdatum}, {doedsort}")
    elif doedsdatum:
        lines.append(f"Died: {doedsdatum}")
    elif doedsort:
        lines.append(f"Died: {doedsort}")

    _append_if(lines, "Killed", rec.get("platsen_stupade", ""))
    _append_if(lines, "Info", rec.get("oevrig_information", ""))

    lines.append("")


def format_faltjagare_results(result: SearchResult) -> str:
    """Format Fältjägare search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more Fältjägare results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No Fältjägare results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Fältjägare search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_faltjagare_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)

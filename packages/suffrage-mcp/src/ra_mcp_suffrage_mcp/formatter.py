"""Plain-text formatters for suffrage search results."""

from __future__ import annotations

from ra_mcp_suffrage_lib.search_operations import SearchResult


def _append_if(lines: list[str], label: str, value: str) -> None:
    """Append 'Label: value' to lines if value is truthy."""
    if value:
        lines.append(f"{label}: {value}")


def _format_contribution(rec: dict) -> str:
    """Format monetary contribution from kr and öre."""
    kr = rec.get("bidrag_kr", "")
    ore = rec.get("bidrag_ore", "")
    if kr and ore:
        return f"{kr} kr {ore} \u00f6re"
    if kr:
        return f"{kr} kr"
    if ore:
        return f"{ore} \u00f6re"
    return ""


def _format_rostratt_record(rec: dict, lines: list[str]) -> None:
    """Format a single Rösträtt record into lines."""
    fornamn = rec.get("fornamn", "")
    efternamn = rec.get("efternamn", "")
    name = " ".join(p for p in [fornamn, efternamn] if p)
    lines.append(f"--- {name} ---")
    _append_if(lines, "Title", rec.get("titel", ""))
    _append_if(lines, "Occupation", rec.get("yrke", ""))
    _append_if(lines, "Address", rec.get("adress", ""))

    ortens_namn = rec.get("ortens_namn", "")
    lan = rec.get("lan", "")
    town_parts = [p for p in [ortens_namn, lan] if p]
    if town_parts:
        lines.append(f"Town: {', '.join(town_parts)}")

    contribution = _format_contribution(rec)
    _append_if(lines, "Contribution", contribution)
    _append_if(lines, "Birth info", rec.get("fodelseuppgift", ""))
    _append_if(lines, "Notes", rec.get("ovriga_anteckningar", ""))
    lines.append("")


def format_rostratt_results(result: SearchResult) -> str:
    """Format Rösträtt search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more R\u00f6str\u00e4tt results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No R\u00f6str\u00e4tt results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(
        f"R\u00f6str\u00e4tt search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})"
    )
    lines.append("")

    for rec in result.records:
        _format_rostratt_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)


def _format_fkpr_record(rec: dict, lines: list[str]) -> None:
    """Format a single FKPR record into lines."""
    foernamn = rec.get("foernamn", "")
    efternamn = rec.get("efternamn", "")
    name = " ".join(p for p in [foernamn, efternamn] if p)
    lines.append(f"--- {name} ---")
    _append_if(lines, "Title", rec.get("titel_yrke", ""))
    _append_if(lines, "Address", rec.get("adress", ""))

    years = rec.get("membership_years", [])
    if years:
        lines.append(f"Member: {', '.join(str(y) for y in years)}")

    _append_if(lines, "Notes", rec.get("anteckningar", ""))
    lines.append("")


def format_fkpr_results(result: SearchResult) -> str:
    """Format FKPR search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more FKPR results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No FKPR results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"FKPR search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_fkpr_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)

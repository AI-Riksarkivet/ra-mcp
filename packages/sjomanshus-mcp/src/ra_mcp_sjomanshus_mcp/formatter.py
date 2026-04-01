"""Plain-text formatters for Sjömanshus search results."""

from __future__ import annotations

from ra_mcp_sjomanshus_lib.search_operations import SearchResult


def _format_name(rec: dict) -> str:
    """Build full name from foernamn, efternamn1, efternamn2."""
    return " ".join(p for p in [rec.get("foernamn", ""), rec.get("efternamn1", ""), rec.get("efternamn2", "")] if p)


def _format_born(rec: dict) -> str:
    """Format birth date and parish."""
    parts = [p for p in [rec.get("foedelsedat", ""), rec.get("foedelsefoers", "")] if p]
    return ", ".join(parts) if parts else ""


def _format_sjomanshus(rec: dict) -> str:
    """Format seamen's house and registration number."""
    sh = rec.get("sjoemanshus", "")
    nr = rec.get("inskrivnr", "")
    parts = []
    if sh:
        parts.append(sh)
    if nr:
        parts.append(f"Nr: {nr}")
    return ", ".join(parts) if parts else ""


def _format_archive(rec: dict) -> str:
    """Format archive reference."""
    arkiv = rec.get("arkiv", "")
    arkivnr = rec.get("arkivnr", "")
    parts = []
    if arkiv:
        parts.append(arkiv)
    if arkivnr:
        parts.append(f"({arkivnr})")
    return " ".join(parts) if parts else ""


def _format_place_date(place: str, date: str) -> str:
    """Format a place with optional date in parentheses."""
    if place and date:
        return f"{place} ({date})"
    return place or date


def _format_ship(rec: dict) -> str:
    """Format ship info: name (type), home port."""
    fartyg = rec.get("fartyg", "")
    typ = rec.get("typ", "")
    hemmahamn = rec.get("hemmahamn", "")
    parts = []
    if fartyg:
        parts.append(f"{fartyg} ({typ})" if typ else fartyg)
    if hemmahamn:
        parts.append(hemmahamn)
    return ", ".join(parts) if parts else ""


def _append_if(lines: list[str], label: str, value: str) -> None:
    """Append 'Label: value' to lines if value is truthy."""
    if value:
        lines.append(f"{label}: {value}")


def _format_liggare_record(rec: dict, lines: list[str]) -> None:
    """Format a single Liggare record into lines."""
    lines.append(f"--- Liggare {rec.get('id', '?')} ---")
    _append_if(lines, "Name", _format_name(rec))
    _append_if(lines, "Rank", rec.get("befattning_yrke", ""))
    _append_if(lines, "Born", _format_born(rec))
    _append_if(lines, "Home", rec.get("hemfoers", ""))
    _append_if(lines, "Ship", _format_ship(rec))

    voyage_from = _format_place_date(rec.get("paamoenstort", ""), rec.get("paamoenstdat", ""))
    voyage_to = _format_place_date(rec.get("avmoenstort", ""), rec.get("avmoenstdat", ""))
    if voyage_from or voyage_to:
        lines.append(f"Voyage: {voyage_from} \u2192 {voyage_to}")

    _append_if(lines, "Destination", rec.get("destination", ""))
    _append_if(lines, "Captain", rec.get("kapten", ""))
    _append_if(lines, "Owner", rec.get("redare", ""))
    _append_if(lines, "Seamen's house", _format_sjomanshus(rec))
    _append_if(lines, "Archive", _format_archive(rec))
    lines.append("")


def format_liggare_results(result: SearchResult) -> str:
    """Format Liggare search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more Liggare results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No Liggare results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Liggare search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_liggare_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)


def _format_matrikel_record(rec: dict, lines: list[str]) -> None:
    """Format a single Matrikel record into lines."""
    lines.append(f"--- Matrikel {rec.get('id', '?')} ---")
    _append_if(lines, "Name", _format_name(rec))
    _append_if(lines, "Born", _format_born(rec))
    _append_if(lines, "Home", rec.get("hemfoers", ""))
    _append_if(lines, "Father", rec.get("far", ""))
    _append_if(lines, "Mother", rec.get("mor", ""))
    _append_if(lines, "Seamen's house", _format_sjomanshus(rec))
    _append_if(lines, "Registered", rec.get("inskrivdat", ""))

    avfoerdort = rec.get("avfoerdort", "")
    avfoerddat = rec.get("avfoerddat", "")
    orsak = rec.get("orsak", "")
    if avfoerdort or avfoerddat or orsak:
        dereg_parts = []
        place_date = _format_place_date(avfoerdort, avfoerddat)
        if place_date:
            dereg_parts.append(place_date)
        if orsak:
            dereg_parts.append(f"Reason: {orsak}")
        lines.append(f"Deregistered: {', '.join(dereg_parts)}")

    _append_if(lines, "Archive", _format_archive(rec))
    lines.append("")


def format_matrikel_results(result: SearchResult) -> str:
    """Format Matrikel search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more Matrikel results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No Matrikel results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Matrikel search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_matrikel_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)

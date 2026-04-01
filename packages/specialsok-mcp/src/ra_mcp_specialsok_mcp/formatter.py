"""Plain-text formatters for Specialsök search results."""

from __future__ import annotations

from ra_mcp_specialsok_lib.search_operations import SearchResult


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len characters, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _append_if(lines: list[str], label: str, value: str) -> None:
    """Append 'Label: value' to lines if value is truthy."""
    if value:
        lines.append(f"{label}: {value}")


def _format_header(dataset: str, result: SearchResult) -> list[str]:
    """Build the standard header lines for a result set."""
    if not result.records:
        if result.offset > 0:
            return [f"No more {dataset} results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"]
        return [f"No {dataset} results found for '{result.keyword}'."]

    lines: list[str] = []
    lines.append(f"{dataset} search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")
    return lines


def _format_footer(result: SearchResult, lines: list[str]) -> None:
    """Append pagination hint if more results exist."""
    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")


# ---------------------------------------------------------------------------
# Flygvapenhaverier formatter
# ---------------------------------------------------------------------------


def _format_flygvapen_record(rec: dict, lines: list[str]) -> None:
    """Format a single Flygvapenhaverier record."""
    lines.append("--- Flygvapenhaveri ---")
    _append_if(lines, "Date", rec.get("datum", ""))
    _append_if(lines, "Aircraft", rec.get("fpl_typ", ""))
    _append_if(lines, "Aircraft no", rec.get("fpl_nr", ""))
    _append_if(lines, "Unit", rec.get("forband_klartext", ""))
    _append_if(lines, "Engine", rec.get("motor_typ", ""))
    _append_if(lines, "Crash site", rec.get("havplats", ""))
    _append_if(lines, "Crew", rec.get("bes_ant", ""))
    _append_if(lines, "Casualties", rec.get("ant_omk", ""))
    _append_if(lines, "Classification", rec.get("klassning", ""))

    sammanfattning = rec.get("sammanfattning", "")
    if sammanfattning:
        lines.append(f"Summary: {_truncate(sammanfattning, 500)}")

    lines.append("")


def format_flygvapen_results(result: SearchResult) -> str:
    """Format Flygvapenhaverier search results as plain text."""
    lines = _format_header("Flygvapenhaverier", result)
    if not result.records:
        return "\n".join(lines)

    for rec in result.records:
        _format_flygvapen_record(rec, lines)
    _format_footer(result, lines)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Fångrullor formatter
# ---------------------------------------------------------------------------


def _format_fangrullor_record(rec: dict, lines: list[str]) -> None:
    """Format a single Fångrullor record."""
    lines.append("--- Fångrulle ---")
    name_parts = [rec.get("fornamn", ""), rec.get("efternamn", "")]
    name = " ".join(p for p in name_parts if p)
    _append_if(lines, "Name", name)
    _append_if(lines, "Age", rec.get("alder", ""))
    _append_if(lines, "Home parish", rec.get("hemort", ""))
    _append_if(lines, "Crime", rec.get("brott", ""))
    _append_if(lines, "Year", rec.get("ar", ""))
    _append_if(lines, "Number", rec.get("nummer", ""))
    lines.append("")


def format_fangrullor_results(result: SearchResult) -> str:
    """Format Fångrullor search results as plain text."""
    lines = _format_header("Fångrullor", result)
    if not result.records:
        return "\n".join(lines)

    for rec in result.records:
        _format_fangrullor_record(rec, lines)
    _format_footer(result, lines)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Kurhuset formatter
# ---------------------------------------------------------------------------


def _format_kurhuset_record(rec: dict, lines: list[str]) -> None:
    """Format a single Kurhuset record."""
    lines.append("--- Kurhuset patient ---")
    name_parts = [rec.get("fornamn", ""), rec.get("efternamn", "")]
    name = " ".join(p for p in name_parts if p)
    _append_if(lines, "Name", name)
    _append_if(lines, "Age", rec.get("alder", ""))
    _append_if(lines, "Title", rec.get("titel", ""))
    _append_if(lines, "Family", rec.get("familj", ""))
    _append_if(lines, "Home (village)", rec.get("hemort_by", ""))
    _append_if(lines, "Home (parish)", rec.get("hemort_socken", ""))
    _append_if(lines, "Admitted", rec.get("inskrivningsdatum", ""))
    _append_if(lines, "Discharged", rec.get("utskrivningsdatum", ""))
    _append_if(lines, "Outcome", rec.get("utskrivningsstatus", ""))
    _append_if(lines, "Days", rec.get("vardtid", ""))
    _append_if(lines, "Disease", rec.get("sjukdom", ""))

    beskrivning = rec.get("sjukdomsbeskrivning", "")
    if beskrivning:
        lines.append(f"Description: {_truncate(beskrivning, 400)}")

    behandling = rec.get("sjukdomsbehandling", "")
    if behandling:
        lines.append(f"Treatment: {_truncate(behandling, 400)}")

    _append_if(lines, "Note", rec.get("anmarkning", ""))
    lines.append("")


def format_kurhuset_results(result: SearchResult) -> str:
    """Format Kurhuset search results as plain text."""
    lines = _format_header("Kurhuset", result)
    if not result.records:
        return "\n".join(lines)

    for rec in result.records:
        _format_kurhuset_record(rec, lines)
    _format_footer(result, lines)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Presskonferenser formatter
# ---------------------------------------------------------------------------


def _format_press_record(rec: dict, lines: list[str]) -> None:
    """Format a single Presskonferens record."""
    lines.append("--- Presskonferens ---")
    _append_if(lines, "Date", rec.get("datum", ""))
    _append_if(lines, "Year", rec.get("aar", ""))
    _append_if(lines, "Title", rec.get("titel", ""))
    _append_if(lines, "Archive", rec.get("arkivbildare", ""))
    _append_if(lines, "RA nr", rec.get("v_ra_nr", ""))

    innehaall = rec.get("innehaall", "")
    if innehaall:
        lines.append(f"Content: {_truncate(innehaall, 500)}")

    _append_if(lines, "Note", rec.get("anmaerkning", ""))
    lines.append("")


def format_press_results(result: SearchResult) -> str:
    """Format Presskonferenser search results as plain text."""
    lines = _format_header("Presskonferenser", result)
    if not result.records:
        return "\n".join(lines)

    for rec in result.records:
        _format_press_record(rec, lines)
    _format_footer(result, lines)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Videobutiker formatter
# ---------------------------------------------------------------------------


def _format_video_record(rec: dict, lines: list[str]) -> None:
    """Format a single Videobutik record."""
    lines.append("--- Videobutik ---")
    _append_if(lines, "Store", rec.get("butiksnamn", ""))
    _append_if(lines, "Company", rec.get("firmanamn", ""))
    _append_if(lines, "Address", rec.get("besoeksadress", ""))
    _append_if(lines, "City", rec.get("ort", ""))
    _append_if(lines, "Municipality", rec.get("kommun", ""))
    _append_if(lines, "County", rec.get("laen", ""))
    _append_if(lines, "Region", rec.get("landsdel", ""))
    _append_if(lines, "Active", rec.get("aktiv", ""))
    _append_if(lines, "Reg nr", rec.get("reg_nr", ""))
    lines.append("")


def format_video_results(result: SearchResult) -> str:
    """Format Videobutiker search results as plain text."""
    lines = _format_header("Videobutiker", result)
    if not result.records:
        return "\n".join(lines)

    for rec in result.records:
        _format_video_record(rec, lines)
    _format_footer(result, lines)
    return "\n".join(lines)

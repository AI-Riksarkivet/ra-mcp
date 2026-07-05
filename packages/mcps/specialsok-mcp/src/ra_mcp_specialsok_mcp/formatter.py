"""Plain-text formatters for Specialsök search results."""

from __future__ import annotations

from typing import Any

from ra_mcp_common.formatting import append_if, truncate_text
from ra_mcp_specialsok_lib.search_operations import SearchResult


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


def _format_flygvapen_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Flygvapenhaverier record."""
    lines.append("--- Flygvapenhaveri ---")
    append_if(lines, "Date", rec.get("datum", ""))
    append_if(lines, "Aircraft", rec.get("fpl_typ", ""))
    append_if(lines, "Aircraft no", rec.get("fpl_nr", ""))
    append_if(lines, "Unit", rec.get("forband_klartext", ""))
    append_if(lines, "Engine", rec.get("motor_typ", ""))
    append_if(lines, "Crash site", rec.get("havplats", ""))
    append_if(lines, "Crew", rec.get("bes_ant", ""))
    append_if(lines, "Casualties", rec.get("ant_omk", ""))
    append_if(lines, "Classification", rec.get("klassning", ""))

    sammanfattning = rec.get("sammanfattning", "")
    if sammanfattning:
        lines.append(f"Summary: {truncate_text(sammanfattning, 200)}")

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


def _format_fangrullor_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Fångrullor record."""
    lines.append("--- Fångrulle ---")
    name_parts = [rec.get("fornamn", ""), rec.get("efternamn", "")]
    name = " ".join(p for p in name_parts if p)
    append_if(lines, "Name", name)
    append_if(lines, "Age", rec.get("alder", ""))
    append_if(lines, "Home parish", rec.get("hemort", ""))
    append_if(lines, "Crime", rec.get("brott", ""))
    append_if(lines, "Year", rec.get("ar", ""))
    append_if(lines, "Number", rec.get("nummer", ""))
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


def _format_kurhuset_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Kurhuset record."""
    lines.append("--- Kurhuset patient ---")
    name_parts = [rec.get("fornamn", ""), rec.get("efternamn", "")]
    name = " ".join(p for p in name_parts if p)
    append_if(lines, "Name", name)
    append_if(lines, "Age", rec.get("alder", ""))
    append_if(lines, "Title", rec.get("titel", ""))
    append_if(lines, "Family", rec.get("familj", ""))
    append_if(lines, "Home (village)", rec.get("hemort_by", ""))
    append_if(lines, "Home (parish)", rec.get("hemort_socken", ""))
    append_if(lines, "Admitted", rec.get("inskrivningsdatum", ""))
    append_if(lines, "Discharged", rec.get("utskrivningsdatum", ""))
    append_if(lines, "Outcome", rec.get("utskrivningsstatus", ""))
    append_if(lines, "Days", rec.get("vardtid", ""))
    append_if(lines, "Disease", rec.get("sjukdom", ""))

    beskrivning = rec.get("sjukdomsbeskrivning", "")
    if beskrivning:
        lines.append(f"Description: {truncate_text(beskrivning, 200)}")

    behandling = rec.get("sjukdomsbehandling", "")
    if behandling:
        lines.append(f"Treatment: {truncate_text(behandling, 200)}")

    append_if(lines, "Note", rec.get("anmarkning", ""))
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


def _format_press_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Presskonferens record."""
    lines.append("--- Presskonferens ---")
    append_if(lines, "Date", rec.get("datum", ""))
    append_if(lines, "Year", rec.get("aar", ""))
    append_if(lines, "Title", rec.get("titel", ""))
    append_if(lines, "Archive", rec.get("arkivbildare", ""))
    append_if(lines, "RA nr", rec.get("v_ra_nr", ""))

    innehaall = rec.get("innehaall", "")
    if innehaall:
        lines.append(f"Content: {truncate_text(innehaall, 200)}")

    append_if(lines, "Note", rec.get("anmaerkning", ""))
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


def _format_video_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Videobutik record."""
    lines.append("--- Videobutik ---")
    append_if(lines, "Store", rec.get("butiksnamn", ""))
    append_if(lines, "Company", rec.get("firmanamn", ""))
    append_if(lines, "Address", rec.get("besoeksadress", ""))
    append_if(lines, "City", rec.get("ort", ""))
    append_if(lines, "Municipality", rec.get("kommun", ""))
    append_if(lines, "County", rec.get("laen", ""))
    append_if(lines, "Region", rec.get("landsdel", ""))
    append_if(lines, "Active", rec.get("aktiv", ""))
    append_if(lines, "Reg nr", rec.get("reg_nr", ""))
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

"""Plain-text formatter for TORA search results."""

from __future__ import annotations

from ra_mcp_tora_lib.models import ToraPlace


def _append_if(lines: list[str], label: str, value: str) -> None:
    if value:
        lines.append(f"{label}: {value}")


def _format_place(place: ToraPlace, lines: list[str]) -> None:
    lines.append(f"--- {place.name} ---")

    accuracy_note = f" ({place.accuracy} accuracy)" if place.accuracy else ""
    lines.append(f"Coordinates: {place.lat}, {place.lon}{accuracy_note}")

    _append_if(lines, "Parish", place.parish)
    _append_if(lines, "Municipality", place.municipality)
    _append_if(lines, "County", place.county)
    _append_if(lines, "Province", place.province)
    lines.append(f"TORA: {place.tora_url}")
    _append_if(lines, "Wikidata", place.wikidata_url)

    if place.images:
        max_shown = 5
        lines.append("")
        lines.append(f"Historical images ({len(place.images)}):")
        for img in place.images[:max_shown]:
            creator = f" by {img.creator}" if img.creator else ""
            period = f" ({img.period})" if img.period else ""
            lines.append(f"  - {img.title}{creator}{period}")
            lines.append(f"    Image: {img.image_url}")
            if img.libris_url:
                lines.append(f"    Libris: {img.libris_url}")
        if len(place.images) > max_shown:
            lines.append(f"  ... and {len(place.images) - max_shown} more")

    lines.append("")


def format_tora_results(query: str, places: list[ToraPlace]) -> str:
    if not places:
        return f"No TORA places found for '{query}'."

    lines: list[str] = []

    if len(places) > 1:
        lines.append(f"TORA: {len(places)} places match '{query}'. Use parish or county to narrow down.")
    else:
        lines.append(f"TORA result for '{query}':")
    lines.append("")

    for place in places:
        _format_place(place, lines)

    return "\n".join(lines)

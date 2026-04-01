"""Plain-text formatters for DDS church records search results."""

from __future__ import annotations

from ra_mcp_dds_lib.search_operations import SearchResult


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
# Födelse (birth) formatter
# ---------------------------------------------------------------------------


def _format_fodelse_record(rec: dict, lines: list[str]) -> None:
    """Format a single Födelse record into lines."""
    lines.append(f"--- F\u00f6delse {rec.get('postid', '?')} ---")

    name = rec.get("fornamn", "")
    kon = rec.get("kon", "")
    if name:
        lines.append(f"Name: {name} ({kon})" if kon else f"Name: {name}")

    _append_if(lines, "Date", rec.get("datum", ""))

    forsamling = rec.get("forsamling", "")
    lan = rec.get("lan", "")
    if forsamling or lan:
        lines.append(f"Parish: {forsamling}, {lan}" if forsamling and lan else f"Parish: {forsamling or lan}")

    # Parents
    far_parts = [rec.get("far_fornamn", ""), rec.get("far_efternamn", "")]
    far_name = " ".join(p for p in far_parts if p)
    far_yrke = rec.get("far_yrke", "")
    if far_name:
        lines.append(f"Father: {far_name}, {far_yrke}" if far_yrke else f"Father: {far_name}")

    mor_parts = [rec.get("mor_fornamn", ""), rec.get("mor_efternamn", "")]
    mor_name = " ".join(p for p in mor_parts if p)
    if mor_name:
        lines.append(f"Mother: {mor_name}")

    _append_if(lines, "Birth place", rec.get("fodelseort", ""))

    anm = rec.get("anm", "")
    if anm:
        lines.append(f"Note: {_truncate(anm, 300)}")

    referenskod = rec.get("referenskod", "")
    volym = rec.get("volym", "")
    if referenskod or volym:
        lines.append(f"Archive: {referenskod}, {volym}" if referenskod and volym else f"Archive: {referenskod or volym}")

    lines.append("")


def format_fodelse_results(result: SearchResult) -> str:
    """Format Födelse search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more F\u00f6delse results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No F\u00f6delse results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"F\u00f6delse search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_fodelse_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Döda (death) formatter
# ---------------------------------------------------------------------------


def _format_doda_record(rec: dict, lines: list[str]) -> None:
    """Format a single Döda record into lines."""
    lines.append(f"--- D\u00f6da {rec.get('postid', '?')} ---")

    name_parts = [rec.get("fornamn", ""), rec.get("efternamn", "")]
    name = " ".join(p for p in name_parts if p)
    _append_if(lines, "Name", name)
    _append_if(lines, "Occupation", rec.get("yrke", ""))
    _append_if(lines, "Date", rec.get("datum", ""))
    _append_if(lines, "Age", rec.get("alder", ""))

    forsamling = rec.get("forsamling", "")
    lan = rec.get("lan", "")
    if forsamling or lan:
        lines.append(f"Parish: {forsamling}, {lan}" if forsamling and lan else f"Parish: {forsamling or lan}")

    _append_if(lines, "Home", rec.get("hemort", ""))

    dodsorsak = rec.get("dodsorsak", "")
    dodsorsak_klass = rec.get("dodsorsak_klassificerat", "")
    if dodsorsak or dodsorsak_klass:
        if dodsorsak and dodsorsak_klass:
            lines.append(f"Cause of death: {dodsorsak} ({dodsorsak_klass})")
        else:
            lines.append(f"Cause of death: {dodsorsak or dodsorsak_klass}")

    # Relative
    anhorig_parts = [rec.get("anhorig_fornamn", ""), rec.get("anhorig_efternamn", "")]
    anhorig_name = " ".join(p for p in anhorig_parts if p)
    anhorig_yrke = rec.get("anhorig_yrke", "")
    anhorig_relation = rec.get("anhorig_relation", "")
    if anhorig_name:
        rel_str = anhorig_name
        if anhorig_yrke:
            rel_str += f", {anhorig_yrke}"
        if anhorig_relation:
            rel_str += f" ({anhorig_relation})"
        lines.append(f"Relative: {rel_str}")

    anm = rec.get("anm", "")
    if anm:
        lines.append(f"Note: {_truncate(anm, 300)}")

    referenskod = rec.get("referenskod", "")
    volym = rec.get("volym", "")
    if referenskod or volym:
        lines.append(f"Archive: {referenskod}, {volym}" if referenskod and volym else f"Archive: {referenskod or volym}")

    lines.append("")


def format_doda_results(result: SearchResult) -> str:
    """Format Döda search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more D\u00f6da results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No D\u00f6da results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"D\u00f6da search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_doda_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Vigsel (marriage) formatter
# ---------------------------------------------------------------------------


def _format_vigsel_record(rec: dict, lines: list[str]) -> None:
    """Format a single Vigsel record into lines."""
    lines.append(f"--- Vigsel {rec.get('postid', '?')} ---")

    _append_if(lines, "Date", rec.get("datum", ""))

    forsamling = rec.get("forsamling", "")
    lan = rec.get("lan", "")
    if forsamling or lan:
        lines.append(f"Parish: {forsamling}, {lan}" if forsamling and lan else f"Parish: {forsamling or lan}")

    # Groom
    bg_parts = [rec.get("brudgum_fornamn", ""), rec.get("brudgum_efternamn", "")]
    bg_name = " ".join(p for p in bg_parts if p)
    if bg_name:
        bg_details = [bg_name]
        bg_yrke = rec.get("brudgum_yrke", "")
        if bg_yrke:
            bg_details.append(bg_yrke)
        bg_alder = rec.get("brudgum_alder", "")
        if bg_alder:
            bg_details.append(f"age {bg_alder}")
        bg_hemort = rec.get("brudgum_hemort", "")
        if bg_hemort:
            bg_details.append(bg_hemort)
        lines.append(f"Groom: {', '.join(bg_details)}")

    # Bride
    br_parts = [rec.get("brud_fornamn", ""), rec.get("brud_efternamn", "")]
    br_name = " ".join(p for p in br_parts if p)
    if br_name:
        br_details = [br_name]
        br_yrke = rec.get("brud_yrke", "")
        if br_yrke:
            br_details.append(br_yrke)
        br_alder = rec.get("brud_alder", "")
        if br_alder:
            br_details.append(f"age {br_alder}")
        br_hemort = rec.get("brud_hemort", "")
        if br_hemort:
            br_details.append(br_hemort)
        lines.append(f"Bride: {', '.join(br_details)}")

    anm = rec.get("anm", "")
    if anm:
        lines.append(f"Note: {_truncate(anm, 300)}")

    referenskod = rec.get("referenskod", "")
    volym = rec.get("volym", "")
    if referenskod or volym:
        lines.append(f"Archive: {referenskod}, {volym}" if referenskod and volym else f"Archive: {referenskod or volym}")

    lines.append("")


def format_vigsel_results(result: SearchResult) -> str:
    """Format Vigsel search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more Vigsel results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No Vigsel results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Vigsel search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_vigsel_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)

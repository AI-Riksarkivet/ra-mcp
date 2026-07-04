"""Plain-text formatters for court records search results."""

from __future__ import annotations

from ra_mcp_court_lib.search_operations import SearchResult


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
# Domboksregister formatter
# ---------------------------------------------------------------------------


def _format_domboksregister_record(rec: dict, lines: list[str]) -> None:
    """Format a single Domboksregister record into lines."""
    lines.append(f"--- Domboksregister {rec.get('id', '?')} ---")

    name_parts = [rec.get("fnamn", ""), rec.get("enamn", "")]
    name = " ".join(p for p in name_parts if p)
    _append_if(lines, "Name", name)
    _append_if(lines, "Title", rec.get("titel", ""))
    _append_if(lines, "Role", rec.get("roll", ""))
    _append_if(lines, "Parish", rec.get("socken", ""))
    _append_if(lines, "Place", rec.get("plats", ""))
    _append_if(lines, "Date", rec.get("datum", ""))
    _append_if(lines, "Case", rec.get("arende", ""))

    anteckning = rec.get("anteckning", "")
    if anteckning:
        lines.append(f"Note: {_truncate(anteckning, 150)}")

    lines.append("")


def format_domboksregister_results(result: SearchResult) -> str:
    """Format Domboksregister search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more Domboksregister results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No Domboksregister results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(
        f"Domboksregister search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})"
    )
    lines.append("")

    for rec in result.records:
        _format_domboksregister_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Medelstad formatter
# ---------------------------------------------------------------------------


def _format_medelstad_record(rec: dict, lines: list[str]) -> None:
    """Format a single Medelstad record into lines."""
    lines.append(f"--- Medelstad {rec.get('lopnr', '?')} ---")

    name_parts = [rec.get("norm_fornamn", ""), rec.get("norm_efternamn", "")]
    name = " ".join(p for p in name_parts if p)
    _append_if(lines, "Name", name)
    _append_if(lines, "Title", rec.get("norm_titel", ""))
    _append_if(lines, "Parish", rec.get("norm_forsamling", ""))
    _append_if(lines, "Place", rec.get("norm_plats", ""))

    ting_dag = rec.get("ting_dag", "")
    ting_typ = rec.get("ting_typ", "")
    if ting_dag or ting_typ:
        court_str = f"{ting_dag} ({ting_typ})" if ting_dag and ting_typ else ting_dag or ting_typ
        lines.append(f"Court: {court_str}")

    mal_typ = rec.get("mal_typ", "")
    mal_nr = rec.get("mal_nr", "")
    if mal_typ or mal_nr:
        case_str = f"{mal_typ} nr {mal_nr}" if mal_typ and mal_nr else mal_typ or mal_nr
        lines.append(f"Case: {case_str}")

    mal_referat = rec.get("mal_referat", "")
    if mal_referat:
        lines.append(f"Summary: {_truncate(mal_referat, 200)}")

    lines.append("")


def format_medelstad_results(result: SearchResult) -> str:
    """Format Medelstad search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more Medelstad results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No Medelstad results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Medelstad search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_medelstad_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)

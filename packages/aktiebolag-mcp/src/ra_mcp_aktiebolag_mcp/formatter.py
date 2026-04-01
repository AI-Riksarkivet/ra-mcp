"""Plain-text formatters for Aktiebolag search results."""

from __future__ import annotations

from ra_mcp_aktiebolag_lib.search_operations import SearchResult


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
# Bolag (company) formatter
# ---------------------------------------------------------------------------


def _format_bolag_record(rec: dict, lines: list[str]) -> None:
    """Format a single Aktiebolag company record into lines."""
    namn = rec.get("bolagets_namn", "?")
    argang = rec.get("argang", "")
    header = f"--- {namn} ({argang}) ---" if argang else f"--- {namn} ---"
    lines.append(header)

    _append_if(lines, "Former name", rec.get("aldre_namn", ""))
    _append_if(lines, "Address", rec.get("postadress", ""))
    _append_if(lines, "Seat", rec.get("styrelsesate", ""))

    andamal = rec.get("bolagets_andamal", "")
    if andamal:
        lines.append(f"Purpose: {_truncate(andamal, 400)}")

    _append_if(lines, "Director", rec.get("verkstall_dir", ""))

    aktiekapital = rec.get("aktiekapital", "")
    if aktiekapital:
        lines.append(f"Capital: {aktiekapital} kr")

    styrelsemedlemmar = rec.get("styrelsemedlemmar", "")
    if styrelsemedlemmar:
        lines.append(f"Board: {_truncate(styrelsemedlemmar, 300)}")

    lines.append("")


def format_bolag_results(result: SearchResult) -> str:
    """Format Aktiebolag company search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more company results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No company results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Company search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_bolag_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Styrelse (board member) formatter
# ---------------------------------------------------------------------------


def _format_styrelse_record(rec: dict, lines: list[str]) -> None:
    """Format a single board member record into lines."""
    styrelsemed = rec.get("styrelsemed", "")
    fornamn = rec.get("fornamn", "")
    name = f"{styrelsemed} {fornamn}".strip() if styrelsemed or fornamn else "?"
    lines.append(f"--- {name} ---")

    _append_if(lines, "Title", rec.get("titel", ""))
    _append_if(lines, "Gender", rec.get("kon", ""))
    _append_if(lines, "Company", rec.get("bolagets_namn", ""))

    lines.append("")


def format_styrelse_results(result: SearchResult) -> str:
    """Format board member search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return f"No more board member results for '{result.keyword}' at offset {result.offset}. Total found: {result.total_hits}"
        return f"No board member results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(f"Board member search results for '{result.keyword}': showing {len(result.records)} of {result.total_hits} records (offset {result.offset})")
    lines.append("")

    for rec in result.records:
        _format_styrelse_record(rec, lines)

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(f"More results available. Use offset={next_offset} to see the next page.")

    return "\n".join(lines)

"""Plain-text formatters for Aktiebolag search results."""

from __future__ import annotations

from typing import Any

from ra_mcp_aktiebolag_lib.search_operations import SearchResult
from ra_mcp_common.formatting import append_if, truncate_text
from ra_mcp_dataset_lib import format_results


# ---------------------------------------------------------------------------
# Bolag (company) formatter
# ---------------------------------------------------------------------------


def _format_bolag_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Aktiebolag company record into lines."""
    namn = rec.get("bolagets_namn", "?")
    argang = rec.get("argang", "")
    header = f"--- {namn} ({argang}) ---" if argang else f"--- {namn} ---"
    lines.append(header)

    append_if(lines, "Former name", rec.get("aldre_namn", ""))
    append_if(lines, "Address", rec.get("postadress", ""))
    append_if(lines, "Seat", rec.get("styrelsesate", ""))

    andamal = rec.get("bolagets_andamal", "")
    if andamal:
        lines.append(f"Purpose: {truncate_text(andamal, 200)}")

    append_if(lines, "Director", rec.get("verkstall_dir", ""))

    aktiekapital = rec.get("aktiekapital", "")
    if aktiekapital:
        lines.append(f"Capital: {aktiekapital} kr")

    styrelsemedlemmar = rec.get("styrelsemedlemmar", "")
    if styrelsemedlemmar:
        lines.append(f"Board: {truncate_text(styrelsemedlemmar, 200)}")

    lines.append("")


def format_bolag_results(result: SearchResult) -> str:
    """Format Aktiebolag company search results as plain text for MCP/LLM consumption."""
    return format_results(result, label="Company", render_record=_format_bolag_record)


# ---------------------------------------------------------------------------
# Styrelse (board member) formatter
# ---------------------------------------------------------------------------


def _format_styrelse_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single board member record into lines."""
    styrelsemed = rec.get("styrelsemed", "")
    fornamn = rec.get("fornamn", "")
    name = f"{styrelsemed} {fornamn}".strip() if styrelsemed or fornamn else "?"
    lines.append(f"--- {name} ---")

    append_if(lines, "Title", rec.get("titel", ""))
    append_if(lines, "Gender", rec.get("kon", ""))
    append_if(lines, "Company", rec.get("bolagets_namn", ""))

    lines.append("")


def format_styrelse_results(result: SearchResult) -> str:
    """Format board member search results as plain text for MCP/LLM consumption."""
    return format_results(result, label="Board member", render_record=_format_styrelse_record)

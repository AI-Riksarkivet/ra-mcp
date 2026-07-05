"""Plain-text formatters for court records search results."""

from __future__ import annotations

from typing import Any

from ra_mcp_common.formatting import append_if, truncate_text
from ra_mcp_court_lib.search_operations import SearchResult
from ra_mcp_dataset_lib import format_results


# ---------------------------------------------------------------------------
# Domboksregister formatter
# ---------------------------------------------------------------------------


def _format_domboksregister_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Domboksregister record into lines."""
    lines.append(f"--- Domboksregister {rec.get('id', '?')} ---")

    name_parts = [rec.get("fnamn", ""), rec.get("enamn", "")]
    name = " ".join(p for p in name_parts if p)
    append_if(lines, "Name", name)
    append_if(lines, "Title", rec.get("titel", ""))
    append_if(lines, "Role", rec.get("roll", ""))
    append_if(lines, "Parish", rec.get("socken", ""))
    append_if(lines, "Place", rec.get("plats", ""))
    append_if(lines, "Date", rec.get("datum", ""))
    append_if(lines, "Case", rec.get("arende", ""))

    anteckning = rec.get("anteckning", "")
    if anteckning:
        lines.append(f"Note: {truncate_text(anteckning, 150)}")

    lines.append("")


def format_domboksregister_results(result: SearchResult) -> str:
    """Format Domboksregister search results as plain text for MCP/LLM consumption."""
    return format_results(result, label="Domboksregister", render_record=_format_domboksregister_record)


# ---------------------------------------------------------------------------
# Medelstad formatter
# ---------------------------------------------------------------------------


def _format_medelstad_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single Medelstad record into lines."""
    lines.append(f"--- Medelstad {rec.get('lopnr', '?')} ---")

    name_parts = [rec.get("norm_fornamn", ""), rec.get("norm_efternamn", "")]
    name = " ".join(p for p in name_parts if p)
    append_if(lines, "Name", name)
    append_if(lines, "Title", rec.get("norm_titel", ""))
    append_if(lines, "Parish", rec.get("norm_forsamling", ""))
    append_if(lines, "Place", rec.get("norm_plats", ""))

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
        lines.append(f"Summary: {truncate_text(mal_referat, 200)}")

    lines.append("")


def format_medelstad_results(result: SearchResult) -> str:
    """Format Medelstad search results as plain text for MCP/LLM consumption."""
    return format_results(result, label="Medelstad", render_record=_format_medelstad_record)

"""Plain-text formatter for SBL search results."""

from __future__ import annotations

from typing import Any

from ra_mcp_dataset_lib import format_results
from ra_mcp_sbl_lib.search_operations import SearchResult


def _format_date(year: int | None, month: int | None, day: int | None, prefix: str = "") -> str:
    """Format a date from separate year/month/day fields.

    Returns a string like '1819-05-17' or '~1750' (with prefix) or '' if no year.
    """
    if year is None:
        return ""
    parts = [str(year)]
    if month is not None:
        parts.append(f"{month:02d}")
        if day is not None:
            parts.append(f"{day:02d}")
    date_str = "-".join(parts)
    if prefix:
        date_str = f"{prefix}{date_str}"
    return date_str


def _format_sbl_record(rec: dict[str, Any], lines: list[str]) -> None:
    """Format a single SBL record into lines."""
    given_name = rec.get("given_name", "")
    surname = rec.get("surname", "")
    name = f"{given_name} {surname}".strip() if given_name else surname
    lines.append(f"--- {name} ---")

    gender = rec.get("gender", "")
    if gender and gender != "-":
        lines.append(f"Gender: {'Male' if gender == 'm' else 'Female' if gender == 'f' else gender}")

    article_type = rec.get("article_type", "")
    if article_type == "Family article":
        lines.append(f"Type: {article_type}")

    occupation = rec.get("occupation", "")
    if occupation:
        lines.append(f"Occupation: {occupation}")

    born = _format_date(
        rec.get("birth_year"),
        rec.get("birth_month"),
        rec.get("birth_day"),
        prefix=rec.get("birth_year_prefix", ""),
    )
    birth_place = rec.get("birth_place", "")
    if born or birth_place:
        born_parts = [p for p in [born, birth_place] if p]
        lines.append(f"Born: {', '.join(born_parts)}")

    died = _format_date(
        rec.get("death_year"),
        rec.get("death_month"),
        rec.get("death_day"),
        prefix=rec.get("death_year_prefix", ""),
    )
    death_place = rec.get("death_place", "")
    if died or death_place:
        died_parts = [p for p in [died, death_place] if p]
        lines.append(f"Died: {', '.join(died_parts)}")

    cv = rec.get("cv", "")
    if cv:
        truncated = cv[:200] + "..." if len(cv) > 200 else cv
        lines.append(f"CV: {truncated}")

    sbl_uri = rec.get("sbl_uri", "")
    if sbl_uri:
        lines.append(f"SBL: {sbl_uri}")

    lines.append("")


def format_sbl_results(result: SearchResult) -> str:
    """Format SBL search results as plain text for MCP/LLM consumption.

    Args:
        result: SearchResult from SBLSearch.search.

    Returns:
        Formatted plain text string.
    """
    return format_results(result, label="SBL", render_record=_format_sbl_record)

"""Plain-text formatter for SDHK and MPO search results."""

from __future__ import annotations

from ra_mcp_diplomatics_lib.search_operations import SearchResult


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len, adding '…' if needed."""
    if not text:
        return ""
    return text[:max_len] + "…" if len(text) > max_len else text


def _escape_pipe(text: str) -> str:
    """Escape pipe characters and newlines for markdown table cells."""
    return text.replace("|", "\\|").replace("\n", " ").replace("\r", "")


def format_sdhk_results(result: SearchResult) -> str:
    """Format SDHK search results as a markdown table for MCP/LLM consumption.

    Args:
        result: SearchResult from DiplomaticsSearch.search_sdhk.

    Returns:
        Markdown-formatted table string.
    """
    if not result.records:
        if result.offset > 0:
            return (
                f"No more SDHK results for '{result.keyword}' at offset {result.offset}. "
                f"Total found: {result.total_hits}"
            )
        return f"No SDHK results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(
        f"SDHK results for '{result.keyword}': "
        f"showing {len(result.records)} of {result.total_hits} "
        f"(offset {result.offset})"
    )
    lines.append("")
    lines.append("PRESENT THESE RESULTS AS A TABLE.")
    lines.append("")

    # Table header
    lines.append("| SDHK | Date | Place | Author | Summary | Status |")
    lines.append("|------|------|-------|--------|---------|--------|")

    for rec in result.records:
        sdhk_id = rec.get("id", "")
        date = _escape_pipe(rec.get("date", "") or "")
        place = _escape_pipe(rec.get("place", "") or "")
        author = _escape_pipe(rec.get("author", "") or "")
        summary = _escape_pipe(_truncate(rec.get("summary", "") or "", 120))

        manifest_url = rec.get("manifest_url", "")
        has_transcription = rec.get("has_transcription", False)
        if manifest_url:
            status = "Digitized + Transcribed" if has_transcription else "Digitized"
        else:
            status = "Not digitized"

        lines.append(
            f"| {sdhk_id} | {date} | {place} | {author} | {summary} | {status} |"
        )

    lines.append("")

    # Detail blocks for records with summaries/editions
    has_details = False
    for rec in result.records:
        summary = rec.get("summary", "") or ""
        edition = rec.get("edition", "") or ""
        manifest_url = rec.get("manifest_url", "")
        if len(summary) > 120 or edition or manifest_url:
            if not has_details:
                lines.append("### Details")
                lines.append("")
                has_details = True
            sdhk_id = rec.get("id", "")
            lines.append(f"**SDHK {sdhk_id}**")
            if summary:
                lines.append(f"Summary: {_truncate(summary, 500)}")
            if edition:
                lines.append(f"Edition: {_truncate(edition, 300)}")
            if manifest_url:
                lines.append(f"IIIF Manifest: {manifest_url}")
            lines.append("")

    # Pagination info
    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(
            f"More results available. Use offset={next_offset} to see the next page."
        )

    return "\n".join(lines)


def format_mpo_results(result: SearchResult) -> str:
    """Format MPO search results as a markdown table for MCP/LLM consumption.

    Args:
        result: SearchResult from DiplomaticsSearch.search_mpo.

    Returns:
        Markdown-formatted table string.
    """
    if not result.records:
        if result.offset > 0:
            return (
                f"No more MPO results for '{result.keyword}' at offset {result.offset}. "
                f"Total found: {result.total_hits}"
            )
        return f"No MPO results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(
        f"MPO results for '{result.keyword}': "
        f"showing {len(result.records)} of {result.total_hits} "
        f"(offset {result.offset})"
    )
    lines.append("")
    lines.append("PRESENT THESE RESULTS AS A TABLE.")
    lines.append("")

    # Table header
    lines.append("| MPO | Category | Dating | Origin | Script | Content |")
    lines.append("|-----|----------|--------|--------|--------|---------|")

    for rec in result.records:
        mpo_id = rec.get("id", "")
        category = _escape_pipe(rec.get("category", "") or "")
        dating = _escape_pipe(rec.get("dating", "") or "")
        origin = _escape_pipe(rec.get("origin_place", "") or "")
        script = _escape_pipe(rec.get("script", "") or "")
        content = _escape_pipe(_truncate(rec.get("content", "") or "", 120))

        lines.append(
            f"| {mpo_id} | {category} | {dating} | {origin} | {script} | {content} |"
        )

    lines.append("")

    # Detail blocks for records with longer content or manifest URLs
    has_details = False
    for rec in result.records:
        content = rec.get("content", "") or ""
        iiif_manifest = rec.get("iiif_manifest", "") or ""
        bildvisning_url = rec.get("bildvisning_url", "") or ""
        title = rec.get("title", "") or ""
        author = rec.get("author", "") or ""
        if len(content) > 120 or iiif_manifest or title:
            if not has_details:
                lines.append("### Details")
                lines.append("")
                has_details = True
            mpo_id = rec.get("id", "")
            lines.append(f"**MPO {mpo_id}**")
            if title:
                lines.append(f"Title: {title}")
            if author:
                lines.append(f"Author: {author}")
            if content:
                lines.append(f"Content: {_truncate(content, 500)}")
            if iiif_manifest:
                lines.append(f"IIIF Manifest: {iiif_manifest}")
            if bildvisning_url:
                lines.append(f"Bildvisning: {bildvisning_url}")
            lines.append("")

    # Pagination info
    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(
            f"More results available. Use offset={next_offset} to see the next page."
        )

    return "\n".join(lines)


def format_sdhk_info(row: dict) -> str:
    """Format an SDHK record as markdown for the viewer info panel."""
    sdhk_id = row.get("id", "?")
    lines: list[str] = [f"## SDHK {sdhk_id}"]

    title = row.get("title", "")
    if title:
        lines.append(f"*{title}*")
    lines.append("")

    for label, key in [
        ("Author", "author"),
        ("Date", "date"),
        ("Place", "place"),
        ("Language", "language"),
        ("Printed", "printed"),
    ]:
        val = row.get(key, "")
        if val:
            lines.append(f"**{label}:** {val}")

    summary = row.get("summary", "")
    if summary:
        lines.append("")
        lines.append("### Summary")
        lines.append(summary)

    edition = row.get("edition", "")
    if edition:
        truncated = edition[:1000] + "..." if len(edition) > 1000 else edition
        lines.append("")
        lines.append("### Edition")
        lines.append(truncated)

    seals = row.get("seals", "")
    if seals:
        lines.append("")
        lines.append("### Seals")
        lines.append(seals)

    return "\n".join(lines)


def format_mpo_info(row: dict) -> str:
    """Format an MPO record as markdown for the viewer info panel."""
    mpo_id = row.get("id", "?")
    lines: list[str] = [f"## MPO {mpo_id}"]

    manuscript_type = row.get("manuscript_type", "")
    if manuscript_type:
        lines.append(f"*{manuscript_type}*")
    lines.append("")

    for label, key in [
        ("Type", "manuscript_type"),
        ("Category", "category"),
        ("Title", "title"),
        ("Author", "author"),
        ("Dating", "dating"),
        ("Origin", "origin_place"),
        ("Institution", "institution"),
        ("Collection", "collection"),
        ("Script", "script"),
        ("Material", "material"),
        ("Notation", "notation"),
        ("Size", "format_size"),
    ]:
        val = row.get(key, "")
        if val:
            lines.append(f"**{label}:** {val}")

    decoration = row.get("decoration", "")
    if decoration:
        lines.append("")
        lines.append("### Decoration")
        lines.append(decoration)

    content = row.get("content", "")
    if content:
        lines.append("")
        lines.append("### Content")
        lines.append(content)

    damage = row.get("damage", "")
    if damage:
        lines.append("")
        lines.append("### Damage")
        lines.append(damage)

    return "\n".join(lines)

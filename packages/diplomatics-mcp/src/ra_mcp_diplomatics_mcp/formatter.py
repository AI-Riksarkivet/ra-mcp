"""Plain-text formatter for SDHK and MPO search results."""

from __future__ import annotations

from ra_mcp_diplomatics_lib.search_operations import SearchResult


def format_sdhk_results(result: SearchResult) -> str:
    """Format SDHK search results as plain text for MCP/LLM consumption.

    Args:
        result: SearchResult from DiplomaticsSearch.search_sdhk.

    Returns:
        Formatted plain text string.
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
        f"SDHK search results for '{result.keyword}': "
        f"showing {len(result.records)} of {result.total_hits} records "
        f"(offset {result.offset})"
    )
    lines.append("")

    for rec in result.records:
        sdhk_id = rec.get("id", "")
        lines.append(f"--- SDHK {sdhk_id} ---")

        title = rec.get("title", "")
        if title:
            lines.append(f"Title: {title}")

        author = rec.get("author", "")
        if author:
            lines.append(f"Author: {author}")

        date = rec.get("date", "")
        if date:
            lines.append(f"Date: {date}")

        place = rec.get("place", "")
        if place:
            lines.append(f"Place: {place}")

        language = rec.get("language", "")
        if language:
            lines.append(f"Language: {language}")

        summary = rec.get("summary", "")
        if summary:
            truncated = summary[:500] + "..." if len(summary) > 500 else summary
            lines.append(f"Summary: {truncated}")

        edition = rec.get("edition", "")
        if edition:
            truncated = edition[:300] + "..." if len(edition) > 300 else edition
            lines.append(f"Edition: {truncated}")

        printed = rec.get("printed", "")
        if printed:
            lines.append(f"Printed: {printed}")

        manifest_url = rec.get("manifest_url", "")
        has_transcription = rec.get("has_transcription", False)

        if manifest_url:
            lines.append(f"IIIF Manifest: {manifest_url}")
            if has_transcription:
                lines.append("Status: Digitized + Transcribed")
            else:
                lines.append("Status: Digitized (no transcription)")
        else:
            lines.append("Status: Not digitized")

        lines.append("")

    # Pagination info
    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(
            f"More results available. Use offset={next_offset} to see the next page."
        )

    return "\n".join(lines)


def format_mpo_results(result: SearchResult) -> str:
    """Format MPO search results as plain text for MCP/LLM consumption.

    Args:
        result: SearchResult from DiplomaticsSearch.search_mpo.

    Returns:
        Formatted plain text string.
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
        f"MPO search results for '{result.keyword}': "
        f"showing {len(result.records)} of {result.total_hits} records "
        f"(offset {result.offset})"
    )
    lines.append("")

    for rec in result.records:
        mpo_id = rec.get("id", "")
        lines.append(f"--- MPO {mpo_id} ---")

        manuscript_type = rec.get("manuscript_type", "")
        if manuscript_type:
            lines.append(f"Type: {manuscript_type}")

        category = rec.get("category", "")
        if category:
            lines.append(f"Category: {category}")

        title = rec.get("title", "")
        if title:
            lines.append(f"Title: {title}")

        author = rec.get("author", "")
        if author:
            lines.append(f"Author: {author}")

        dating = rec.get("dating", "")
        if dating:
            lines.append(f"Dating: {dating}")

        origin = rec.get("origin_place", "")
        if origin:
            lines.append(f"Origin: {origin}")

        collection = rec.get("collection", "")
        if collection:
            lines.append(f"Collection: {collection}")

        institution = rec.get("institution", "")
        if institution:
            lines.append(f"Institution: {institution}")

        script = rec.get("script", "")
        if script:
            lines.append(f"Script: {script}")

        material = rec.get("material", "")
        if material:
            lines.append(f"Material: {material}")

        content = rec.get("content", "")
        if content:
            truncated = content[:500] + "..." if len(content) > 500 else content
            lines.append(f"Content: {truncated}")

        iiif_manifest = rec.get("iiif_manifest", "")
        if iiif_manifest:
            lines.append(f"IIIF Manifest: {iiif_manifest}")

        bildvisning_url = rec.get("bildvisning_url", "")
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

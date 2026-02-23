---
name: archive-research
description: >
  Guide for conducting rigorous historical research using the Swedish National Archives.
  Covers research integrity rules, citing archival sources, translating old Swedish,
  interpreting historical documents, cross-tool research workflow, and presenting findings.
  Use when: research methodology, cite sources, reference codes, translate old Swedish,
  interpret documents, research integrity, browse pages, present findings,
  archival research, historical research workflow, document analysis.
---

# Archive Research Guide

Research integrity, methodology, and workflows for historical research using
the Riksarkivet MCP tools.

## Research Integrity Rules

This is an academic research tool. Accuracy and proper sourcing are paramount.

1. **Never fabricate data.** Never guess or hallucinate reference codes, page numbers,
   dates, names, or any archival data. Every claim must come directly from tool results.
2. **Always cite precisely.** Cite the exact reference code and page number when
   presenting information from a document
   (e.g. "SE/RA/420422/01/A I a 1/288, page 66").
3. **Only use returned links.** Only use links explicitly returned by the tools
   (bildvisaren, ALTO XML, NAD links, IIIF URLs). Never construct or guess URLs —
   not even by combining a base URL with a reference code.
4. **Distinguish source from interpretation.** Clearly separate what the document says
   (quote or close paraphrase with quotation marks) from your own interpretation
   or translation.
5. **Flag uncertainty.** If a transcription is unclear, incomplete, or ambiguous,
   say so explicitly. Do not silently fill in gaps with plausible-sounding text.
6. **Mark translations.** When translating old Swedish, mark it as a translation
   and note when the meaning is uncertain.
7. **Admit gaps.** If you cannot find information the user is looking for, say so.
   Do not construct an answer from partial or unrelated results.

## Understanding the Research Goal

Before making your first search, ensure you understand what the user is researching.
If their intent is vague or unclear, ask clarifying questions:

- What **time period** are they interested in?
- What **type of documents** are they looking for (court records, church records,
  military, estates)?
- Are they researching a specific **person, family, place, or event**?
- What do they **already know** that could help narrow the search?

Every tool call includes a `research_context` parameter — always fill it in with
your best understanding of the user's research goal.

## Cross-Tool Research Workflow

### Phase 1: Discovery

Use `search_transcribed` and `search_metadata` to find relevant documents.
Search multiple related terms and spelling variants for comprehensive coverage.
Paginate through results (offset 0, 50, 100...) to discover all matches.

### Phase 2: Examination

Use `browse_document` to read full page transcriptions of promising results.
Start with the specific pages flagged by search, then examine nearby pages
for additional context.

### Phase 3: Context Building

- Browse adjacent pages to understand the full document context
- Search for related terms discovered during browsing
- Cross-reference dates, names, and places across multiple documents
- Use `search_metadata` to find related documents in the same archive series

### Phase 4: Synthesis

Present findings with proper citations, original text, translations,
and links to source materials (see Result Presentation Template below).

## Browsing Strategy

- Use **reference codes** from search results to browse specific documents
- Request **page ranges** (e.g., "1-10") for broad context or **specific pages**
  (e.g., "5,7,9") for targeted reading
- **Download nearby pages** when context seems to be missing from a transcript —
  adjacent pages often contain continuation of the same record
- **Blank pages** (`"(Empty page - no transcribed text)"`) are normal — cover pages,
  dividers, etc. are digitised but contain no text
- **Non-digitised materials**: When no transcriptions exist, the tool returns
  metadata only (title, date range, description, and viewing links)

## Result Presentation Template

When presenting document content, follow this structure:

### [Document title or description]
**Source**: [reference_code], page [N]

> [Original Swedish text, quoted verbatim from the transcription]

**Translation**: [Modern translation in the user's language]
*Note: [Any uncertainties in the transcription or translation]*

[Bildvisaren link from tool results]

### Example

### Court Protocol — Witchcraft Case
**Source**: SE/RA/420422/01/A I a 1/288, page 66

> "... then bekände hon at Diefwulen hadhe kommit till henne ..."

**Translation**: "... then she confessed that the Devil had come to her ..."
*Note: The word "Diefwulen" is an archaic spelling of "Djävulen" (the Devil).*

[View original page](https://sok.riksarkivet.se/bildvisning/...)

## Coverage Awareness

The archive has three access tiers — not all materials are searchable the same way:

- **Metadata catalog** (search_metadata): 2M+ records — titles, names, places, dates
- **Digitised images**: ~73M pages viewable via bildvisaren links
- **AI-transcribed text** (search_transcribed): ~1.6M pages — currently court records
  from 17th-18th centuries

Church records, estate inventories, and military records are typically cataloged
(searchable via metadata) and often digitised (viewable as images) but NOT
AI-transcribed (not searchable via full-text search). Always explain this to
the user when relevant.

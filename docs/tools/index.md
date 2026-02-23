---
icon: lucide/wrench
---

# Tools & Skills

ra-mcp provides MCP tools for searching, browsing, transcribing, and viewing historical documents, plus skills that guide AI assistants through research workflows.

---

## MCP Tools

### search_transcribed

Search AI-transcribed text in digitised historical documents from the Swedish National Archives. Supports Solr query syntax.

!!! warning "Transcriptions are AI-generated"
    All searchable text was produced by HTR (Handwritten Text Recognition) and OCR models. These transcriptions contain recognition errors — misread characters, merged or split words, and garbled passages are common. **Always use fuzzy search (`~`)** to compensate for errors and significantly increase hits. For example, `stockholm~1` instead of `Stockholm`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search term or Solr query. Supports wildcards (`*`), fuzzy (`~`), Boolean (`AND/OR/NOT`), proximity (`"term1 term2"~N`). |
| `offset` | int | *(required)* | Pagination start position. Use 0 for first page, then 50, 100, etc. |
| `limit` | int | 25 | Maximum documents to return per query. |
| `sort` | str | `relevance` | Sort order: `relevance`, `timeAsc`, `timeDesc`, `alphaAsc`, `alphaDesc`. |
| `year_min` | int \| None | None | Start year filter (e.g. 1700). |
| `year_max` | int \| None | None | End year filter (e.g. 1750). |
| `max_snippets_per_record` | int | 3 | Maximum matching pages shown per document. |
| `max_response_tokens` | int | 15000 | Maximum tokens in response. |
| `dedup` | bool | True | Session deduplication. True compacts already-seen documents. |
| `research_context` | str \| None | None | Brief summary of the user's research goal. |

**Example:**

```
search_transcribed(
    keyword='("Stockholm trolldom"~10)',
    offset=0,
    year_min=1600,
    year_max=1699,
    sort="timeAsc"
)
```

### search_metadata

Search document metadata (titles, names, places, descriptions) across the Swedish National Archives catalog. Covers 2M+ records.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Free-text search across all metadata fields. |
| `offset` | int | *(required)* | Pagination start position. |
| `name` | str \| None | None | Person name filter (e.g. `Nobel`, `Linné`). |
| `place` | str \| None | None | Place name filter (e.g. `Stockholm`, `Göteborg`). |
| `only_digitised` | bool | True | True = digitised only. False = all 2M+ records. |
| *(plus shared params: limit, sort, year_min, year_max, dedup, research_context)* | | | |

**Tip**: Most person/place matches are NOT digitised. Set `only_digitised=False` when using `name` or `place` to avoid empty results.

### browse_document

View full page transcriptions of a document by reference code.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reference_code` | str | *(required)* | Document reference code (e.g. `SE/RA/420422/01`). |
| `pages` | str | *(required)* | Page specification: single (`5`), range (`1-10`), or comma-separated (`5,7,9`). |
| `highlight_term` | str \| None | None | Optional keyword to highlight in the transcription. |
| `max_pages` | int | 20 | Maximum pages to retrieve. |
| `dedup` | bool | True | Session deduplication. Re-browsing pages returns stubs. |
| `research_context` | str \| None | None | Brief summary of the user's research goal. |

**Token cost**: ~300 tokens overhead + ~200-1500 per page. Dense court protocols average ~1000 tokens each.

### htr_transcribe

Transcribe handwritten document images using AI-powered handwritten text recognition (HTRflow).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_urls` | list[str] | *(required)* | Image URLs to process (http/https). |
| `language` | str | `swedish` | Document language: `swedish`, `norwegian`, `english`, `medieval`. |
| `layout` | str | `single_page` | Page layout: `single_page` or `spread` (two-page opening). |
| `export_format` | str | `alto_xml` | Archival export: `alto_xml`, `page_xml`, `json`. |
| `custom_yaml` | str \| None | None | Optional HTRflow YAML pipeline config. Overrides language/layout. |

**Returns**: URLs to an interactive viewer, per-page JSON transcriptions, and an archival export file.

### view_document

Display document pages with zoomable images and text layer overlays in an interactive viewer.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_urls` | list[str] | *(required)* | One image URL per page. |
| `text_layer_urls` | list[str] | *(required)* | One ALTO/PAGE XML URL per page, paired 1:1 with `image_urls`. Use `""` for missing. |
| `metadata` | list[str] \| None | None | Per-page labels (reference codes, descriptions). |

Both lists must have the same length.

---

## Skills (Claude Code Plugin)

Skills are loaded from the [ra-mcp-tools plugin](https://github.com/AI-Riksarkivet/ra-mcp/tree/main/plugins/ra-mcp-tools) and provide research methodology guidance.

### /archive-search

Essential pre-search guide. Covers tool selection (`search_transcribed` vs `search_metadata`), Solr query syntax, wildcards, fuzzy matching for OCR/HTR errors, old Swedish spelling variants (präst/prest, silver/silfver), proximity search, Boolean operators, and pagination workflows.

### /archive-research

Research methodology guide. Covers research integrity rules (never fabricate data, always cite precisely), cross-tool research workflow (discover, examine, contextualize, synthesize), browsing strategy, result presentation with proper citations, and archive coverage awareness.

### /htr-transcription

HTR workflow guide. Covers the full pipeline: determine image source, batch images into a single `htr_transcribe` call, present results as an interactive artifact. Documents language options, layout modes, export formats, and custom HTRflow YAML pipelines.

### /view-document-guide

Document viewer guide. Covers the `view_document` tool's arguments, pairing rules, and common mistakes.

### /upload-files

File upload guide. Covers uploading local files or attachments to get public URLs for HTR or the viewer.

# MCP Tools

Detailed parameter reference for all MCP tools provided by ra-mcp.

---

## search_transcribed

Search AI-transcribed text in digitised historical documents from the Swedish National Archives. Space-separated terms are all required (implicit AND); wildcards, fuzzy and exact phrases are supported. Boolean operators (`AND`/`OR`/`NOT`) are **not** — the API matches them as literal words, so such queries are rejected with a corrective message.

!!! warning "Transcriptions are AI-generated"
    All searchable text was produced by HTR (Handwritten Text Recognition) and OCR models. These transcriptions contain recognition errors — misread characters, merged or split words, and garbled passages are common. **Always use fuzzy search (`~`)** to compensate for errors and significantly increase hits. For example, `stockholm~1` instead of `Stockholm`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `keyword` | str | *(required)* | Search terms — all must match (implicit AND). Supports wildcards (`*`, `?`), fuzzy (`~1`), exact phrases (`"..."`). No `AND`/`OR`/`NOT`; for OR run separate searches. |
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

## search_metadata

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

## browse_document

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

## htr_transcribe

Transcribe handwritten document images using AI-powered handwritten text recognition (HTRflow).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_urls` | list[str] | *(required)* | Image URLs to process (http/https). |
| `language` | str | `swedish` | Document language: `swedish`, `norwegian`, `english`, `medieval`. |
| `layout` | str | `single_page` | Page layout: `single_page` or `spread` (two-page opening). |
| `export_format` | str | `alto_xml` | Archival export: `alto_xml`, `page_xml`, `json`. |
| `custom_yaml` | str \| None | None | Optional HTRflow YAML pipeline config. Overrides language/layout. |

**Returns**: URLs to an interactive viewer, per-page JSON transcriptions, and an archival export file.

## view_document

Display document pages with zoomable images and text layer overlays in an interactive viewer.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_urls` | list[str] | *(required)* | One image URL per page. |
| `text_layer_urls` | list[str] | *(required)* | One ALTO/PAGE XML URL per page, paired 1:1 with `image_urls`. Use `""` for missing. |
| `metadata` | list[str] \| None | None | Per-page labels (reference codes, descriptions). |

Both lists must have the same length.

The viewer module also exposes two convenience entry points that open the same viewer from a different reference:

- **view_manifest** — `manifest_url` (full IIIF manifest URL, e.g. SDHK/MPO results); optional `highlight_term`.
- **view_bild** — `bild_ids` (one or more bildvisning image IDs, e.g. `C0056829_00001`).

In addition the viewer registers app-control tools used by the running MCP App UI (`load_page`, `load_thumbnails`, `search_all_pages`, `viewer_navigate`, `viewer_go_to_page`, `viewer_set_highlight`, `viewer_reopen`, `get_viewer_state`).

## display_pdf

Open a PDF in an interactive PDF.js viewer (search, navigation, annotations) running as an MCP App.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | *(bundled default)* | URL to a PDF file (direct links and academic sources supported). |
| `title` | str \| None | None | Optional display title for the PDF. |

Companion PDF tools:

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `search_pdf` | `url`, `term` | Find a term within a previously opened PDF. |
| `read_pdf_page` | `url`, `page`, `count` (≤5) | Extract text from page(s) of a PDF. |
| `list_pdfs` | — | List PDFs available in the gallery (bundled Riksarkivet guides). |

The PDF module also registers app-control tools (`pdf_go_to_page`, `pdf_set_search`, `get_pdf_state`, `get_page_blocks`, `read_pdf_bytes`, `search_guides`).

## Dataset tools

When the optional dataset modules are installed, the server exposes namespaced search tools over local LanceDB datasets (see [Data Sources](../how-it-works/data-sources.md#local-lancedb-datasets) for coverage figures). Most follow a shared shape: a free-text `keyword`, `offset`/`limit` pagination, a `research_context`, and dataset-specific filters (e.g. `socken`/parish, `roll`/role, `datum_from`/`datum_till` date range on `court:search_domboksregister`).

| Module | Tools |
|--------|-------|
| `diplomatics` | `search_sdhk`, `search_mpo`, `view_sdhk`, `view_mpo` |
| `sbl` | `search_sbl`, `view_sbl_article`, `load_sbl_article` |
| `sjomanshus` | `search_liggare`, `search_matrikel` |
| `filmcensur` | `search_filmreg` |
| `rosenberg` | `search_rosenberg` |
| `court` | `search_domboksregister`, `search_medelstad` |
| `aktiebolag` | `search_bolag`, `search_styrelse` |
| `faltjagare` | `search_faltjagare` |
| `suffrage` | `search_rostratt`, `search_fkpr` |
| `specialsok` | `search_flygvapen`, `search_fangrullor`, `search_kurhuset`, `search_press`, `search_video` |
| `dds` | `search_fodelse`, `search_doda`, `search_vigsel` |
| `wincars` | `search_wincars` |
| `sj` | `search_juda`, `search_ritningar` |
| `tora` | `search_tora` |

Note that `sbl` tools are exposed without a namespace prefix (e.g. `search_sbl`, not `sbl:search_sbl`); all other dataset tools are namespaced by module.

## import_to_label_studio

Imports document pages (images plus optional ALTO transcription) into a Label Studio project for human annotation and transcription feedback. Provided by the optional `label` module.

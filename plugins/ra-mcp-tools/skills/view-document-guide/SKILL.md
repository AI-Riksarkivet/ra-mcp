---
name: view_document-guide
description: Guide for the document viewer tools. Use when the user asks to "view document", "display pages", "show document", "document viewer", "view manifest", or wants to visually inspect document pages. Covers reference-code, manifest, and raw-URL entry points.
---

# Document Viewer Tools

Three tools open the interactive document viewer. Choose based on what you have:

| Tool | When to use |
|------|-------------|
| `view_document` | You have a Riksarkivet reference code (e.g. from search results) |
| `view_manifest` | You have a IIIF manifest URL (e.g. from SDHK/MPO search or any IIIF source) |
| `view_document_urls` | You already have raw image URLs and text layer XML URLs |

All tools render the same interactive viewer with zoomable images, text-layer overlays (when ALTO XML is available), search, info panel, and fullscreen.

---

## `view_document` — From Reference Code

Resolves a Riksarkivet reference code into IIIF image URLs and ALTO XML text layers automatically via BrowseOperations.

### Required Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `reference_code` | string | Archive reference code (e.g. `"SE/RA/420422/01"`) |
| `pages` | string | Page spec: `"5"`, `"1-10"`, or `"5,7,9"` |

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `highlight_term` | string | null | Pre-populate search bar and highlight matches |
| `max_pages` | int | 20 | Maximum pages to retrieve (max: 20) |

### Examples

```json
{"reference_code": "SE/RA/420422/01", "pages": "7"}
```

```json
{"reference_code": "SE/RA/420422/01", "pages": "1-10", "highlight_term": "Stockholm"}
```

```json
{"reference_code": "SE/RA/310187/1", "pages": "5,7,9"}
```

---

## `view_manifest` — From IIIF Manifest URL

Fetches a IIIF manifest, extracts page images and ALTO text layers (from `seeAlso`), and opens the viewer. Works with any IIIF Presentation API v3 manifest — Riksarkivet, Wellcome Collection, or other providers.

### Required Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `manifest_url` | string | Full IIIF manifest URL |

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `highlight_term` | string | null | Pre-populate search bar and highlight matches |
| `max_pages` | int | 20 | Maximum pages to load (max: 20) |

### Examples

Riksarkivet police records (with ALTO transcription):
```json
{"manifest_url": "https://lbiiif.riksarkivet.se/arkis!30002056/manifest"}
```

SDHK medieval charter (image only, no transcription):
```json
{"manifest_url": "https://lbiiif.riksarkivet.se/sdhk!85/manifest"}
```

SDHK with Transkribus transcription (from Hugging Face):
```json
{"manifest_url": "https://huggingface.co/buckets/Riksarkivet/sdhk_hack/resolve/transkribus/manifests/sdhk_R0001691.json"}
```

Wellcome Collection (external provider, with ALTO):
```json
{"manifest_url": "https://iiif.wellcomecollection.org/presentation/b18035723", "max_pages": 10}
```

Note: Documents with ALTO XML in the manifest's `seeAlso` will have text overlays and transcription. Documents without show images only.

---

## `view_document_urls` — From Raw URLs

Use when you already have image and text layer URLs (e.g. from external sources or manual construction). Prefer `view_manifest` when you have a manifest URL.

### Required Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `image_urls` | list[string] | One image URL per page (JPEG or PNG) |
| `text_layer_urls` | list[string] | One XML URL per page (ALTO/PAGE), paired 1:1 with `image_urls`. Use `""` for pages without transcription |

**Both lists must have the same length.**

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `document_info` | string | null | Markdown-formatted document metadata for the info panel |
| `highlight_term` | string | null | Pre-populate search bar and highlight matches |

### Examples

```json
{
  "image_urls": ["https://lbiiif.riksarkivet.se/arkis!R0001203_00007/full/max/0/default.jpg"],
  "text_layer_urls": ["https://sok.riksarkivet.se/dokument/alto/R000/R0001203/R0001203_00007.xml"]
}
```

With document info:

```json
{
  "image_urls": ["https://example.com/page1.jpg", "https://example.com/page2.jpg"],
  "text_layer_urls": ["https://example.com/page1.xml", ""],
  "document_info": "## My Document\n\n**Date:** 1902\n\n**Source:** Example archive"
}
```

---

## `viewer_go_to_page` — Jump to a Page in Open Viewer

**Use this when the user asks to "go to page 3" or "show page 5".** Does NOT replace the loaded pages — just scrolls to that page within the already-loaded document.

| Argument | Type | Description |
|----------|------|-------------|
| `page` | integer | Page number (1-based) |

```json
{"page": 3}
```

---

## `viewer_set_highlight` — Change Highlight in Open Viewer

**IMPORTANT: Use this instead of calling `view_document`/`view_document_urls` again when the viewer is already open and the user just wants to highlight a different term.** Calling the original tools again creates a duplicate viewer.

| Argument | Type | Description |
|----------|------|-------------|
| `highlight_term` | string | Search term to highlight. Use `""` to clear. |

```json
{"highlight_term": "göteborg"}
```

---

## `viewer_navigate` — Navigate to Different Pages in Open Viewer

**IMPORTANT: Use this instead of calling `view_document` again when the viewer is already open and the user wants to see different pages.** Calling the original tool again creates a duplicate viewer.

| Argument | Type | Description |
|----------|------|-------------|
| `reference_code` | string | Archive reference code |
| `pages` | string | Page spec: `"5"`, `"1-10"`, or `"5,7,9"` |
| `highlight_term` | string (optional) | Search term to highlight |

```json
{"reference_code": "SE/RA/420422/01", "pages": "20-30", "highlight_term": "Stockholm"}
```

---

## Typical Workflow

1. **Search** with `search_transcribed`, `search_metadata`, or `diplomatics:search_sdhk` to find documents.
2. **Browse** with `browse_document` to read the transcription text.
3. **View** with `view_document` (reference code), `view_manifest` (IIIF URL), or `view_document_urls` (raw URLs).
4. **Update** with `viewer_set_highlight` or `viewer_navigate` to change what's displayed without creating a new viewer.

## When to Use Which Tool

| Scenario | Tool |
|----------|------|
| Have a reference code from search | `view_document` |
| Have a IIIF manifest URL (SDHK, MPO, Wellcome, etc.) | `view_manifest` |
| Have raw image/ALTO URLs | `view_document_urls` |
| User asks to "go to page 3" | `viewer_go_to_page` |
| User asks to highlight/search a different term | `viewer_set_highlight` |
| User says "show the viewer again" / "open the document" | `viewer_reopen` |
| User asks to load a different set of pages | `viewer_navigate` or `viewer_navigate_urls` |
| User asks to view a completely different document | `view_document`, `view_manifest`, or `view_document_urls` |

**Key rule: Never call the entry-point tools twice in the same conversation if the viewer is already open. Use the update tools instead.**

## Common Mistakes

| Mistake | Fix |
|---|---|
| Calling `view_document` again to change the highlight | Use `viewer_set_highlight` — it updates the existing viewer without creating a duplicate. |
| Calling `view_document` again to show different pages | Use `viewer_navigate` — it updates the existing viewer. |
| Using `view_document` with a manifest URL | Use `view_manifest` for IIIF manifest URLs. `view_document` takes `reference_code` + `pages`. |
| Using `view_document` with a manifest ID like `30002056` | Use a full reference code like `SE/RA/...`. Get it from search results. |
| Mismatched list lengths in `view_document_urls` | Every `image_urls` entry needs a corresponding `text_layer_urls` entry. |
| Forgetting `""` for missing text layers | Use an empty string — do not omit the entry or use `null`. |
| Using `highlight_term` on pages without text layers | Highlights require ALTO/PAGE XML. Pages with `""` text layers won't have matches. |

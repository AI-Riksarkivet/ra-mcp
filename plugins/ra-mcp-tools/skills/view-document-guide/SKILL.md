---
name: view_document-guide
description: Guide for the view_document and view_document_urls tools. Use when the user asks to "view document", "display pages", "show document", "document viewer", or wants to visually inspect document pages. Covers both the reference-code API and the raw-URL API.
---

# Document Viewer Tools

Two tools open the interactive document viewer. Choose based on what you have:

| Tool | When to use |
|------|-------------|
| `view_document` | You have a Riksarkivet reference code (e.g. from search results) |
| `view_document_urls` | You already have raw image URLs and text layer XML URLs |

Both tools render the same interactive viewer with zoomable images, text-layer overlays, search, and fullscreen.

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

## `view_document_urls` — From Raw URLs

Use when you already have image and text layer URLs (e.g. from IIIF manifests, external sources, or manual construction).

### Required Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `image_urls` | list[string] | One image URL per page (JPEG or PNG) |
| `text_layer_urls` | list[string] | One XML URL per page (ALTO/PAGE), paired 1:1 with `image_urls`. Use `""` for pages without transcription |

**Both lists must have the same length.**

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `metadata` | list[string] | null | Per-page labels paired 1:1 with `image_urls` |
| `highlight_term` | string | null | Pre-populate search bar and highlight matches |

### Examples

Single page:

```json
{
  "image_urls": ["https://lbiiif.riksarkivet.se/arkis!R0001203_00007/full/max/0/default.jpg"],
  "text_layer_urls": ["https://sok.riksarkivet.se/dokument/alto/R000/R0001203/R0001203_00007.xml"]
}
```

Multi-page with mixed transcription availability:

```json
{
  "image_urls": [
    "https://lbiiif.riksarkivet.se/arkis!30002056_00010/full/max/0/default.jpg",
    "https://lbiiif.riksarkivet.se/arkis!30002056_00011/full/max/0/default.jpg",
    "https://lbiiif.riksarkivet.se/arkis!30002056_00012/full/max/0/default.jpg"
  ],
  "text_layer_urls": [
    "https://sok.riksarkivet.se/dokument/alto/3000/30002056/30002056_00010.xml",
    "",
    "https://sok.riksarkivet.se/dokument/alto/3000/30002056/30002056_00012.xml"
  ]
}
```

With metadata labels and search highlight:

```json
{
  "image_urls": [
    "https://lbiiif.riksarkivet.se/arkis!30002056_00010/full/max/0/default.jpg",
    "https://lbiiif.riksarkivet.se/arkis!30002056_00011/full/max/0/default.jpg"
  ],
  "text_layer_urls": [
    "https://sok.riksarkivet.se/dokument/alto/3000/30002056/30002056_00010.xml",
    "https://sok.riksarkivet.se/dokument/alto/3000/30002056/30002056_00011.xml"
  ],
  "metadata": ["Page 10 (SE/RA/...)", "Page 11 (SE/RA/...)"],
  "highlight_term": "trolldom"
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

1. **Search** with `search_transcribed` or `search_metadata` to find documents.
2. **Browse** with `browse_document` to read the transcription text.
3. **View** with `view_document` to visually inspect pages with zoomable images and text overlays.
4. **Update** with `viewer_set_highlight` or `viewer_navigate` to change what's displayed without creating a new viewer.

If you already have URLs (e.g. from a IIIF manifest or previous browse result), use `view_document_urls` directly.

## When to Use Which Tool

| Scenario | Tool |
|----------|------|
| First time viewing a document | `view_document` or `view_document_urls` |
| User asks to "go to page 3" | `viewer_go_to_page` |
| User asks to highlight/search a different term | `viewer_set_highlight` |
| User asks to load a different set of pages | `viewer_navigate` or `viewer_navigate_urls` |
| User asks to view a completely different document | `view_document` or `view_document_urls` |

**Key rule: Never call `view_document`/`view_document_urls` twice in the same conversation if the viewer is already open. Use the update tools instead.**

## Common Mistakes

| Mistake | Fix |
|---|---|
| Calling `view_document` again to change the highlight | Use `viewer_set_highlight` — it updates the existing viewer without creating a duplicate. |
| Calling `view_document` again to show different pages | Use `viewer_navigate` — it updates the existing viewer. |
| Using `view_document` with a manifest ID like `30002056` | Use a full reference code like `SE/RA/...`. Get it from search results. |
| Mismatched list lengths in `view_document_urls` | Every `image_urls` entry needs a corresponding `text_layer_urls` entry. |
| Forgetting `""` for missing text layers | Use an empty string — do not omit the entry or use `null`. |
| Using `highlight_term` on pages without text layers | Highlights require ALTO/PAGE XML. Pages with `""` text layers won't have matches. |
| Passing raw URLs to `view_document` | Use `view_document_urls` for raw URLs. `view_document` takes `reference_code` + `pages`. |

---
name: view_document-guide
description: Guide for the view_document tool. Use when the user asks to "view document", "display pages", "show document", "document viewer", or provides image/XML URLs to display in an interactive viewer. Covers required arguments, pairing rules, metadata, and common mistakes.
---

# Using the `view_document` Tool

The `view_document` tool opens an interactive viewer with zoomable page images and optional text-layer overlays (for search, selection, and accessibility).

## Required Arguments

### `image_urls` (list of strings)

One publicly accessible image URL per page (JPEG or PNG).

### `text_layer_urls` (list of strings)

One XML URL per page (ALTO v4 or PAGE XML), paired 1:1 with `image_urls`.
Use an empty string `""` for pages that have no transcription.

**Both lists must have the same length.**

## Optional Arguments

### `metadata` (list of strings | null)

Short per-page labels paired 1:1 with `image_urls`. Use for filenames, archive
reference codes, brief descriptions, etc. Shown in the viewer header. Keep values
short. When omitted the viewer shows no label.

### `highlight_term` (string | null)

A search term to pre-populate the search bar and highlight matching text lines
on the initial page. The viewer also performs a cross-page search across all
pages, showing match-count badges on thumbnails and enabling prev/next
navigation between pages with matches.

### `highlight_term_color` (string | null)

Hex color for search highlights (default: amber `#f59e0b`). Only applies when
`highlight_term` is set.

## Minimal Example — Single Page

```json
{
  "image_urls": [
    "https://example.com/page1.jpg"
  ],
  "text_layer_urls": [
    "https://example.com/page1_alto.xml"
  ]
}
```

## Multi-Page Example — 3 Pages

Page 2 has no transcription; metadata provides archive references.

```json
{
  "image_urls": [
    "https://example.com/page1.jpg",
    "https://example.com/page2.jpg",
    "https://example.com/page3.jpg"
  ],
  "text_layer_urls": [
    "https://example.com/page1_alto.xml",
    "",
    "https://example.com/page3_alto.xml"
  ],
  "metadata": [
    "SE/RA/420422/01/A I a 1/288 p.1",
    "SE/RA/420422/01/A I a 1/288 p.2",
    "SE/RA/420422/01/A I a 1/288 p.3"
  ]
}
```

## Example — With Search Highlight

Pre-populate the search bar so matching lines are highlighted immediately.
The viewer will also search all pages and show badges on thumbnails with matches.

```json
{
  "image_urls": [
    "https://example.com/page1.jpg",
    "https://example.com/page2.jpg"
  ],
  "text_layer_urls": [
    "https://example.com/page1_alto.xml",
    "https://example.com/page2_alto.xml"
  ],
  "highlight_term": "Stockholm"
}
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Mismatched list lengths | Every `image_urls` entry needs a corresponding `text_layer_urls` entry (and `metadata` entry if metadata is provided). |
| Non-public image URLs | The viewer runs client-side. URLs must be publicly accessible without authentication. |
| Forgetting `""` for missing text layers | Use an empty string — do not omit the entry or use `null`. |
| Overly long metadata | Keep metadata to a short label. Long strings get truncated in the viewer header. |
| Setting `highlight_term_color` without `highlight_term` | The color only applies when a search term is provided. |
| Using `highlight_term` without text layers | Highlights require ALTO/PAGE XML text layers. Pages with `""` text layers won't have matches. |

---
name: pdf-guide
description: Guide for the PDF viewer tools. Use when the user asks to "show PDF", "open PDF", "search in PDF", "list PDFs", "visa PDF", "medeltid guide", "slaktforskning guide", or wants to read/search Riksarkivet's PDF publications. Also use when deciding between view_document (archival pages) vs display_pdf (full PDF documents).
---

# PDF Viewer Tools

| Tool | When to use |
|------|-------------|
| `display_pdf` | Open a PDF in the interactive viewer (creates the viewer) |
| `list_pdfs` | See what PDFs/guides are available |
| `search_pdf` | Search text across ALL pages of a loaded PDF |
| `read_pdf_page` | Read the text content of a specific page |
| `pdf_go_to_page` | Navigate the viewer to a specific page |
| `pdf_set_search` | Highlight a search term in the viewer |

---

## When to Use PDF Tools vs Document Viewer

| User intent | Tool |
|-------------|------|
| "Show me the medieval guide" / "visa medeltidsguiden" | `display_pdf` with medeltid URL |
| "What PDFs do you have?" | `list_pdfs` |
| "Search for Gustav Vasa in the PDF" | `search_pdf` (after display_pdf) |
| "What does page 42 say?" | `read_pdf_page` |
| "Go to page 42" | `pdf_go_to_page` |
| "Show me archival document SE/RA/420422/01" | `view_document` (NOT display_pdf) |

**Key distinction:**
- `display_pdf` = full PDF files (books, guides, papers)
- `view_document` = individual archival pages (IIIF images + ALTO XML text)

---

## `display_pdf` — Open a PDF

**IMPORTANT: Always call this first.** All other PDF tools require a PDF to be loaded.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `url` | string | No | URL to PDF file (defaults to Medeltidens samhalle) |
| `title` | string | No | Display title |

```json
{"url": "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/216090389-e30a88-medeltidens-samhalle.pdf?download=true", "title": "Medeltidens samhalle"}
```

---

## `search_pdf` — Search All Pages

Searches ALL pages server-side. Returns per-page match counts and text snippets.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `url` | string | Yes | Same URL used in `display_pdf` |
| `term` | string | Yes | Text to search for |

---

## `read_pdf_page` — Read Page Text

Returns the full text content of a page. Use this to read what's on a page — model context is NOT sent automatically.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `url` | string | Yes | Same URL used in `display_pdf` |
| `page` | int | Yes | Page number (1-based) |

---

## `pdf_go_to_page` / `pdf_set_search` — Navigate & Highlight

Navigate the viewer or highlight text. No AppConfig — reuses existing viewer.

```json
// Navigate
{"page": 42}

// Highlight
{"search_term": "kungamakt"}
```

---

## Available PDFs

- **Hur riket styrdes** — Swedish governance 1520-1920 (255 pages, 63MB)
- **Medeltidens samhalle** — Medieval Sweden guide (258 pages, 5MB) — DEFAULT
- **Ingang till samisk historia** — Sami history guide (2024)

---

## Typical Workflow

1. Call `display_pdf` with the URL (or default)
2. Call `search_pdf` to find where a topic appears
3. Call `read_pdf_page` to read specific pages
4. Call `pdf_go_to_page` + `pdf_set_search` to navigate/highlight viewer
5. Quote the text from `read_pdf_page` results

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Not calling `display_pdf` first | Always call it before search/read/navigate |
| Searching the archive when user asks about a PDF guide | Use PDF tools, not search_transcribed |
| Not using `read_pdf_page` to get page text | Model context is NOT sent automatically — you must call read_pdf_page |
| Calling `display_pdf` twice | Call once, then use navigation/search tools |

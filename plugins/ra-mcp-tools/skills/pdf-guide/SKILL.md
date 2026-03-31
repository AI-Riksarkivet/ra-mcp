---
name: pdf-guide
description: Guide for the PDF viewer tools. Use when the user asks to "show PDF", "open PDF", "search in PDF", "list PDFs", "visa PDF", "medeltid guide", "slaktforskning guide", or wants to read/search Riksarkivet's PDF publications. Also use when deciding between view_document (archival pages) vs display_pdf (full PDF documents).
---

# PDF Viewer Tools

Three tools for working with PDF documents:

| Tool | When to use |
|------|-------------|
| `list_pdfs` | User asks what PDFs/guides are available, or you need to find the right PDF |
| `display_pdf` | Open a PDF in the interactive viewer (from URL) |
| `search_pdf` | Search text across ALL pages of a loaded PDF |

---

## When to Use PDF Tools vs Document Viewer

| User intent | Tool |
|-------------|------|
| "Show me the medieval guide" / "visa medeltidsguiden" | `list_pdfs` → `display_pdf` |
| "Search for Gustav Vasa in the PDF" | `search_pdf` (after display_pdf) |
| "What does page 5 say?" | Read model context (page text is sent automatically) |
| "Show me archival document SE/RA/420422/01" | `view_document` (NOT display_pdf) |
| "Show me this IIIF image" | `view_document_urls` (NOT display_pdf) |
| "Open this PDF: https://..." | `display_pdf` |

**Key distinction:**
- `display_pdf` = full PDF files (books, guides, papers)
- `view_document` = individual archival pages (IIIF images + ALTO XML text)

---

## `list_pdfs` — Discover Available PDFs

Returns Riksarkivet's curated PDF collection. Always call this first when the user asks about guides or publications.

Available PDFs include:
- **Hur riket styrdes** — Swedish governance 1520-1920 (255 pages)
- **Medeltidens samhalle** — Medieval Sweden: charters, royal power, church, cities
- **Ingang till samisk historia** — Sami history in the archives (2024)
- **Slaktforskarna och Krigsarkivet** — Genealogy & military archives (2026)
- **Attention Is All You Need** — Transformer architecture paper

### Example

```json
// No arguments needed
{}
```

Returns list of `{url, title, description, category}`. Use the `url` with `display_pdf`.

---

## `display_pdf` — Open a PDF

Opens the interactive PDF viewer with page navigation, zoom, search, and text extraction.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `url` | string | Yes | URL to PDF file |
| `title` | string | No | Display title |

After calling `display_pdf`:
- The viewer sends **current page text** to model context automatically
- Use `search_pdf` to search across all pages
- Use `interact` to navigate, highlight, or annotate

### Example

```json
{"url": "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/216090389-e30a88-medeltidens-samhalle.pdf?download=true", "title": "Medeltidens samhalle"}
```

---

## `search_pdf` — Search All Pages

Searches text across ALL pages using server-side pymupdf. Fast (~2-5 seconds for 255 pages).

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `url` | string | Yes | Same URL used in `display_pdf` |
| `term` | string | Yes | Text to search for |

Returns `{pageMatches: [{pageNum, matchCount}], totalMatches}`.

### Example

```json
{"url": "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve/Hur%20riket%20styrdes_63MB.pdf?download=true", "term": "Gustav Vasa"}
```

---

## `interact` — Navigate & Annotate

Send commands to the active PDF viewer.

| Action | Required params | Description |
|--------|----------------|-------------|
| `navigate` | `page` (1-based) | Go to a specific page |
| `search` | `query` | Set search term |
| `highlight_text` | `query` | Find and highlight text |
| `add_annotations` | `annotations` array | Add highlights, notes, stamps |
| `zoom` | `scale` (e.g. 1.5) | Set zoom level |

### Example

```json
{"view_uuid": "...", "action": "navigate", "page": 42}
```

The `view_uuid` is returned by `display_pdf` in the text response.

---

## Typical Workflow

1. User asks about a topic → call `list_pdfs` to find relevant PDF
2. Found a match → call `display_pdf` with the URL
3. User asks "what does it say about X?" → call `search_pdf` to find pages
4. Navigate to the page with matches → call `interact` with `navigate`
5. Read the page text from model context → quote the relevant section

### Example Conversation

**User:** "Visa mig guiden om medeltiden"
1. Call `list_pdfs` → find "Medeltidens samhalle"
2. Call `display_pdf(url=..., title="Medeltidens samhalle")`

**User:** "Vad star det om kungamakten?"
1. Call `search_pdf(url=..., term="kungamakt")` → found on pages 15, 22, 45
2. Call `interact(view_uuid=..., action="navigate", page=15)`
3. Read page 15 text from model context → answer the question

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Searching the archive when user asks about a PDF guide | Use `list_pdfs` + `display_pdf` + `search_pdf` |
| Calling `display_pdf` twice (creates duplicate viewer) | Call it once, then use `interact` to navigate |
| Not knowing what PDFs are available | Always call `list_pdfs` first |
| Using `view_document` to open a PDF file | `view_document` is for archival IIIF pages, not PDF files |
| Forgetting to use `search_pdf` when user asks about PDF content | `search_pdf` searches ALL pages server-side in ~2-5 seconds |

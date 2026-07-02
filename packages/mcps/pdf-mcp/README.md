# ra-mcp-pdf-mcp

Interactive PDF viewer MCP App with search, block overlays, and PDF.js rendering.

## Overview

An MCP App that renders an interactive PDF viewer (Svelte UI + PDF.js) directly inside the MCP host (Claude, ChatGPT, etc.). Uses FastMCP's `AppConfig` to serve a self-contained HTML/JS viewer that streams PDF bytes on demand, renders pages with PDF.js, and overlays structured text blocks with highlightable search matches.

The package ships a curated gallery of Riksarkivet archival PDF guides (medieval Sweden, governance, Sami history, genealogy, and more). When a PDF is opened, its DataLab block JSON is prefetched and cached so search and page-text extraction are fast and server-side. The guide JSONs are preloaded into a block cache, which lets `search_guides` and `read_pdf_page` work across all guides without first opening a viewer. View state is held in an async key-value store so the UI can poll for LLM-initiated changes (navigation, highlight).

## MCP Tools

### Open and read (user-visible)

| Tool | Key parameters | Purpose |
|------|----------------|---------|
| `display_pdf` | `url=<default guide>`, `title?` | **Required first step** to open a PDF in the viewer; schedules prefetch of block data |
| `list_pdfs` | *(none)* | List the curated gallery of available Riksarkivet PDF guides |
| `search_guides` | `term` | Search across ALL preloaded guides at once (no `display_pdf` needed); returns guide title, page, snippets |
| `read_pdf_page` | `url`, `page`, `count=1` (max 5) | Read structured text for one or more pages (loads gallery PDFs on demand) |
| `search_pdf` | `url`, `term` | Search all pages of a loaded PDF; per-page match counts and snippets (requires `display_pdf`) |

### Control an open viewer (user-visible)

| Tool | Key parameters | Purpose |
|------|----------------|---------|
| `pdf_set_search` | `search_term` | Highlight a term (or clear with `""`) in the open viewer (requires `display_pdf`) |
| `pdf_go_to_page` | `page` | Navigate the open viewer to a page (requires `display_pdf`) |

### Used by the viewer UI (app-visible only)

| Tool | Key parameters | Purpose |
|------|----------------|---------|
| `read_pdf_bytes` | `url`, `offset=0` | Stream a chunk of PDF bytes (base64) with pagination metadata |
| `get_pdf_state` | `view_id` | Poll current viewer state by view id |
| `get_page_blocks` | `url`, `page` | Get structured blocks (bbox + type) for a page for overlay rendering |

## Architecture

This is an **MCP App** — it uses FastMCP's `AppConfig` and a `ui://` resource:

```
Model calls display_pdf
    |
    v
Tool persists PdfViewerState, schedules block prefetch, returns text summary (model) + structured content (UI)
    |
    v
MCP host renders ui://pdf-viewer/mcp-app.html
    |
    v
Viewer UI streams read_pdf_bytes, fetches get_page_blocks, polls get_pdf_state on demand
```

The HTML viewer is built into `src/ra_mcp_pdf_mcp/dist/mcp-app.html` and served as the `ui://pdf-viewer/mcp-app.html` resource, with a Content-Security-Policy that allows the Hugging Face domains the gallery PDFs are hosted on.

## Components

- **tools.py**: Tool and resource registrations (all `*_pdf*` tools plus the UI resource)
- **cache.py**: Chunked PDF byte fetching (`read_pdf_range`), block cache, prefetch scheduling, and guide preloading (`preload_all_guides`)
- **gallery.py**: The curated gallery of Riksarkivet PDF guides (`GALLERY_ITEMS`, `get_gallery_items`)
- **search.py**: Block-level page search (`search_pages`) and HTML-to-text extraction
- **models.py**: `PdfViewerState` and related data models
- **state.py**: Async key-value store for viewer state (`get_state`, `put_state`, `get_active_state`)
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3001)
python -m ra_mcp_pdf_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_pdf_mcp.server --port 3001

# stdio transport
python -m ra_mcp_pdf_mcp.server --stdio
```

## Dependencies

- External: `httpx[http2]`, `fastmcp`, `py-key-value-aio[memory]`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with no namespace (tools are registered at the root level). Enabled by default. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

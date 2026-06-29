# ra-mcp-viewer-mcp

Interactive document viewer MCP App with zoomable images and text layer overlays.

## Overview

An MCP App that renders an interactive document viewer directly inside the MCP host (Claude, ChatGPT, etc.). Uses FastMCP's `AppConfig` to serve a self-contained HTML/JS viewer that displays high-resolution page images with optional ALTO/PAGE XML text layer overlays for search, highlighting, and accessibility.

There are several entry points depending on what you have: a reference code (`view_document`), a IIIF manifest URL (`view_manifest`), a `bild_id` image identifier (`view_bild`), or raw paired image/text-layer URLs (`view_document_urls`). Once a viewer is open, a set of `viewer_*` tools mutate the live view (navigate pages, change the highlight, reopen fullscreen) instead of opening a new one. The viewer lazy-loads pages, thumbnails, and per-page search results via app-visible tools it calls on demand. View state is persisted in an async key-value store so the UI can poll for LLM-initiated changes.

## MCP Tools

### Open the viewer (user-visible)

| Tool | Key parameters | Purpose |
|------|----------------|---------|
| `view_document` | `reference_code`, `pages`, `highlight_term?`, `max_pages=20` | Resolve a reference code + page spec (same as `browse_document`) and open the viewer |
| `view_document_urls` | `image_urls`, `text_layer_urls`, `document_info?`, `highlight_term?` | Open the viewer from raw paired image and ALTO/PAGE XML URLs (use `""` for pages without transcription) |
| `view_manifest` | `manifest_url`, `highlight_term?`, `max_pages=20`, `document_info?` | Open the viewer from a IIIF manifest URL (e.g. SDHK/MPO results) |
| `view_bild` | `bild_ids`, `highlight_term?` | Open the viewer by `bild_id` image identifier(s) (e.g. `C0056829_00001` from DDS church records) |

### Control an open viewer (user-visible)

| Tool | Key parameters | Purpose |
|------|----------------|---------|
| `viewer_navigate` | `reference_code`, `pages`, `highlight_term?`, `max_pages=20` | Replace the open viewer's pages with new ones by reference code |
| `viewer_navigate_urls` | `image_urls`, `text_layer_urls`, `highlight_term?` | Replace the open viewer's pages with new raw URLs |
| `viewer_go_to_page` | `page` | Scroll the open viewer to a page (does not reload pages) |
| `viewer_set_highlight` | `highlight_term` | Update (or clear) the search highlight in the open viewer |
| `viewer_reopen` | *(none)* | Bring the open viewer back to fullscreen |

### Used by the viewer UI (app-visible only)

| Tool | Key parameters | Purpose |
|------|----------------|---------|
| `get_viewer_state` | `view_id` | Poll current viewer state by view id |
| `load_page` | `image_url`, `text_layer_url`, `page_index` | Fetch a single page (image + parsed text layer) for pagination |
| `load_thumbnails` | `image_urls`, `page_indices` | Batch-fetch and resize thumbnails for the thumbnail strip |
| `search_all_pages` | `text_layer_urls`, `term` | Search a term across all pages, returning per-page match counts |

## Architecture

This is an **MCP App** — it uses FastMCP's `AppConfig` and a `ui://` resource:

```
Model calls view_document / view_manifest / view_bild / view_document_urls
    |
    v
Tool resolves pages, persists ViewerState, returns text summary (model) + structured content (UI)
    |
    v
MCP host renders ui://document-viewer/mcp-app.html
    |
    v
Viewer UI calls load_page / load_thumbnails / search_all_pages / get_viewer_state on demand
```

The HTML viewer is built into `src/ra_mcp_viewer_mcp/dist/mcp-app.html` and served as the `ui://document-viewer/mcp-app.html` resource.

## Components

- **tools.py**: Tool and resource registrations (all `view_*`, `viewer_*`, and app-visible tools, plus the UI resource)
- **resolve.py**: Resolves reference codes, IIIF manifests, and `bild_id`s into image/text-layer URLs; validates URL pairs
- **fetchers.py**: Async functions for fetching page data, parsing text layers, and building thumbnail data URLs
- **formatter.py**: Builds the text summaries and `ToolResult` helpers returned to the model
- **models.py**: `ViewerState` and related data models
- **state.py**: Async key-value store for viewer state (`get_state`, `put_state`, `get_active_state`)
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# HTTP transport (default, port 3001)
python -m ra_mcp_viewer_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_viewer_mcp.server --port 3001

# stdio transport
python -m ra_mcp_viewer_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-browse-lib`, `ra-mcp-iiif-lib`, `ra-mcp-xml`
- External: `httpx[http2]`, `fastmcp`, `pillow`, `py-key-value-aio[memory]`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with no namespace (tools are registered at the root level). Enabled by default. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

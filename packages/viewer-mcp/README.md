# ra-mcp-viewer-mcp

Interactive document viewer MCP App with zoomable images and text layer overlays.

## Overview

An MCP App that renders an interactive document viewer directly inside the MCP host (Claude, ChatGPT, etc.). Uses FastMCP's `AppConfig` to serve a self-contained HTML/JS viewer that displays high-resolution page images with optional ALTO/PAGE XML text layer overlays for search, selection, and accessibility.

The viewer supports lazy-loading pages and thumbnails via app-visible tools that the UI calls on demand.

## MCP Tools

### `view-document` (user-visible)

Entry point for displaying document pages. Returns page 1 transcription to the model and renders the viewer UI.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_urls` | list[str] | *(required)* | One image URL per page |
| `text_layer_urls` | list[str] | *(required)* | One ALTO/PAGE XML URL per page (paired 1:1 with `image_urls`). Use `""` for pages without transcription. |
| `metadata` | list[str] \| None | None | Per-page labels (e.g., archive reference codes) |

Both lists must have the same length.

### `load-page` (app-visible only)

Fetches a single page on demand — called by the viewer UI for pagination.

### `load-thumbnails` (app-visible only)

Batch-fetches thumbnail images — called by the viewer UI for the thumbnail strip.

## Architecture

This is an **MCP App** — it uses FastMCP's `AppConfig` and `ui://` resources:

```
Model calls view-document
    |
    v
Tool returns: text summary (for model) + structured content (for UI)
    |
    v
MCP host renders ui://document-viewer/mcp-app.html
    |
    v
Viewer UI calls load-page / load-thumbnails via callServerTool
```

The HTML viewer is built from `src/ra_mcp_viewer_mcp/dist/mcp-app.html` and served as a `ui://` resource.

## Components

- **tools.py**: Tool and resource registrations (`view-document`, `load-page`, `load-thumbnails`, UI resource)
- **fetchers.py**: Async functions for fetching page data, text layers, and thumbnail images
- **parser.py**: ALTO/PAGE XML parser
- **models.py**: Data models

## Dependencies

- External: `fastmcp`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with no namespace (tools are registered at the root level). Enabled by default. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

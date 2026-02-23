# ra-mcp-htr-mcp

MCP tool for handwritten text recognition (HTR) via a remote Gradio Space.

## Overview

Provides the `htr_transcribe` MCP tool that sends document images to a remote [HTRflow Gradio Space](https://huggingface.co/spaces/Riksarkivet/htr-demo) for AI-powered handwritten text recognition. Returns URLs to an interactive viewer, per-page JSON transcriptions, and an archival export file.

## MCP Tools

### `htr_transcribe`

Transcribe handwritten document images. Accepts http/https image URLs and returns result file URLs.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_urls` | list[str] | *(required)* | Image URLs to process |
| `language` | str | `swedish` | `swedish`, `norwegian`, `english`, or `medieval` |
| `layout` | str | `single_page` | `single_page` or `spread` (two-page opening) |
| `export_format` | str | `alto_xml` | `alto_xml`, `page_xml`, or `json` |
| `custom_yaml` | str \| None | None | HTRflow YAML pipeline config (overrides language/layout) |

**Returns** (`HtrResult`):

| Field | Description |
|-------|-------------|
| `viewer_url` | Interactive gallery viewer with polygon overlays, search, and confidence scores |
| `pages_url` | JSON with per-page transcription lines (id, text, confidence per line) |
| `export_url` | Archival export file in the requested format |
| `export_format` | Echoed back export format |

## Components

- **tools.py**: FastMCP server setup, `htr_transcribe` tool registration, and `HtrResult` model
- **server.py**: Standalone entry point for isolated dev/testing

## Standalone Usage

```bash
# stdio transport
python -m ra_mcp_htr_mcp.server --stdio

# HTTP transport
python -m ra_mcp_htr_mcp.server --port 3002
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HTR_SPACE_URL` | `https://riksarkivet-htr-demo.hf.space` | Gradio Space URL |
| `HTR_TIMEOUT` | `300` | Transcription timeout in seconds |

## Dependencies

- External: `fastmcp`, `gradio-client`, `pydantic`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with namespace `htr`. Enabled by default. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

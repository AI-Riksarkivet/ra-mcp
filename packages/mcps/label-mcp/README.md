# ra-mcp-label-mcp

MCP tool for importing Riksarkivet document pages into Label Studio as annotation tasks.

## Overview

Registers a single FastMCP tool — `import_to_label_studio` — that pushes document pages to a Label Studio project for human annotation. It supports two modes:

- **ALTO pre-annotation**: given ALTO XML URLs (paired with image URLs), it fetches the XML, converts each page to VectorLabels polygons with transcriptions, and imports them as pre-annotated tasks ready for review and correction.
- **Image-only**: given image URLs alone, it creates blank tasks (just the image) for annotation from scratch.

Pages can optionally be assigned to a Label Studio user, tagged with per-page feedback choices (`Transcription` / `Segmentation`), or previewed as JSON without importing (`dry_run`). Connection settings (URL, token, project) can be passed as arguments or supplied via environment variables (a `.env` file in the package root is auto-loaded).

## MCP Tools

### `import_to_label_studio`

Import pages to a Label Studio project for human annotation. Returns a summary with per-task links, or — in dry-run mode — the converted tasks as JSON.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_urls` | list[str] | *(required)* | Image URLs to import (one per page) |
| `alto_urls` | list[str] \| None | None | ALTO XML URLs paired by index with `image_urls`. If provided, creates pre-annotated VectorLabels tasks; if omitted, creates blank image-only tasks |
| `feedback` | list[list[str]] \| None | None | Per-page feedback choices (`Transcription`, `Segmentation`), paired by index. Requires `alto_urls` |
| `ls_url` | str \| None | None | Label Studio URL (falls back to `LS_URL`) |
| `ls_token` | str \| None | None | Label Studio access token (falls back to `LS_TOKEN`) |
| `project_id` | int \| None | None | Label Studio project ID (falls back to `LS_PROJECT_ID`) |
| `assign_to` | str \| None | None | Email of a Label Studio user to assign the imported tasks to |
| `dry_run` | bool | False | If true, return the converted tasks as JSON without importing |

Validation: `alto_urls` must match `image_urls` in length; `feedback` must match `alto_urls` in length and requires `alto_urls`.

## Components

- **label_tool.py**: `register_label_tool` — `import_to_label_studio` tool, mode selection, validation, import/assign orchestration, and `.env` autoload
- **converter.py**: `convert_alto_to_tasks` / `tasks_to_json` — ALTO XML → VectorLabels pre-annotation tasks
- **ls_client.py**: `import_tasks` / `assign_tasks` — Label Studio SDK calls
- **tools.py**: FastMCP server setup and tool registration
- **server.py**: Standalone entry point for isolated dev/testing

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LS_URL` | Label Studio base URL (e.g. `https://your-ls.hf.space`) |
| `LS_TOKEN` | Label Studio access token |
| `LS_PROJECT_ID` | Default Label Studio project ID |

A `.env` file in the package root is auto-loaded at import time (existing environment variables take precedence).

## Standalone Usage

```bash
# stdio transport (default)
python -m ra_mcp_label_mcp.server

# HTTP transport
python -m ra_mcp_label_mcp.server --port 3003
```

## Dependencies

- Internal: `ra-mcp-common`
- External: `fastmcp`, `httpx`, `label-studio-sdk`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with namespace `label`. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

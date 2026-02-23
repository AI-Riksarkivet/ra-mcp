# ra-mcp-browse-cli

CLI command for browsing Riksarkivet document pages.

## Overview

Provides the `ra browse` command — a terminal interface to the same browse operations used by the MCP tools. Displays page transcriptions with Rich formatting, optional keyword highlighting, and direct links to source images.

## Usage

```bash
ra browse "SE/RA/310187/1" --page "7,8,52"
ra browse "SE/RA/420422/01" --pages "1-10"
ra browse "SE/RA/310187/1" --page "7" --search-term "Stockholm"
ra browse "SE/RA/420422/01" --pages "1-5" --show-links
ra browse "SE/RA/123" --page 1 --log
```

## Page Specification

The `--pages` / `--page` flags accept three formats:

| Format | Example | Description |
|--------|---------|-------------|
| Single | `"5"` | One page |
| Range | `"1-10"` | Pages 1 through 10 |
| List | `"5,7,9"` | Specific pages |

`--page` and `--pages` are interchangeable aliases.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--pages` / `--page` | `1-20` | Page specification (see above) |
| `--search-term` | None | Highlight keyword in transcribed text (case-insensitive) |
| `--max-display` | 20 | Maximum pages to display |
| `--show-links` | off | Display ALTO XML, IIIF image, and Bildvisaren URLs |
| `--log` | off | Enable API request/response logging to `ra_mcp_api.log` |

## Components

- **app.py**: Typer sub-app registration
- **browse_cmd.py**: `ra browse` command implementation with Rich progress spinner
- **formatter.py**: `RichConsoleFormatter` — formatted page output with highlighting

## Dependencies

- Internal: `ra-mcp-browse`
- External: `typer`, `rich`

## Part of ra-mcp

Install with `uv pip install ra-mcp[cli]`. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

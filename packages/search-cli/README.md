# ra-mcp-search-cli

CLI command for searching Riksarkivet transcribed documents.

## Overview

Provides the `ra search` command — a terminal interface to the same search operations used by the MCP tools. Uses Rich for formatted output with document tables, snippet previews, and pagination stats.

## Usage

```bash
ra search "Stockholm"
ra search "trolldom" --limit 50
ra search "(Stockholm AND trolldom)" --limit 25
ra search "Stockholm" --text --include-all-materials
ra search "Stockholm" --max-hits-per-vol 1 --limit 100
ra search "Stockholm" --log
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | 25 | Maximum records to fetch from API (pagination size) |
| `--max-display` | 10 | Maximum records to display in output |
| `--max-hits-per-vol` | 3 | Limit hits per volume (useful for broad searches) |
| `--transcribed-text` / `--text` | `--transcribed-text` | Search AI-transcribed text (default) or metadata fields |
| `--only-digitised-materials` / `--include-all-materials` | `--only-digitised-materials` | Limit to digitised materials or include all records |
| `--log` | off | Enable API request/response logging to `ra_mcp_api.log` |

**Note**: `--transcribed-text` requires `--only-digitised-materials`. Using `--include-all-materials` automatically switches to `--text`.

## Components

- **app.py**: Typer sub-app registration
- **search_cmd.py**: `ra search` command implementation with Rich progress spinner
- **formatter.py**: `RichConsoleFormatter` — formatted tables and summary stats

## Dependencies

- Internal: `ra-mcp-search`
- External: `typer`, `rich`

## Part of ra-mcp

Install with `uv pip install ra-mcp[cli]`. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

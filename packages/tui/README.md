# ra-mcp-tui

Interactive terminal browser for the Swedish National Archives (Riksarkivet).

## Overview

A full-featured Textual TUI application for searching and browsing Riksarkivet documents directly in the terminal. Supports both transcribed text and metadata search, document browsing with page navigation, and keyboard-driven workflows.

## Usage

```bash
ra tui                # Launch empty TUI
ra tui "trolldom"     # Launch with pre-filled search
ra tui "Stockholm"    # Search on launch
```

## Screens

- **Search**: Full-text search with mode toggle (transcribed / metadata), paginated result list, and metadata preview panel
- **Document**: Document detail view with metadata and page list
- **Page Viewer**: Full page transcription display with navigation

## Keybindings

| Key | Action |
|-----|--------|
| `/` | Focus search input |
| `Enter` | Submit search / Open selected item |
| `Escape` | Go back / Clear search |
| `m` | Toggle search mode (Transcribed / Metadata) |
| `n` / `p` | Next / Previous page of results |
| `o` | Open in browser (works on all screens) |
| `y` | Copy reference code to clipboard |
| `c` | Copy page text to clipboard (page viewer) |
| `a` | Copy ALTO XML URL to clipboard (page viewer) |
| `?` | Show keybindings help |
| `q` | Quit |

## Components

- **app.py**: Main `RiksarkivetApp` — Textual application with custom Riksarkivet theme
- **cli.py**: `ra tui` Typer command registration
- **services.py**: `ArchiveService` — bridge between TUI and domain packages
- **screens/**: `SearchScreen`, `DocumentScreen`, `PageScreen`
- **widgets/**: `SearchBar`, `ResultList`, `MetadataPanel`, `PageViewer`, `HelpOverlay`

## Dependencies

- Internal: `ra-mcp-search`, `ra-mcp-browse`
- External: `textual`, `typer`

## Part of ra-mcp

Install with `uv pip install ra-mcp[tui]`. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

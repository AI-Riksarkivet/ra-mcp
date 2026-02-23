# ra-mcp-browse-mcp

MCP tool for browsing Riksarkivet document pages.

## Overview

Thin MCP wrapper around `ra-mcp-browse`. Registers the `browse_document` FastMCP tool that retrieves full page transcriptions with session-based deduplication, keyword highlighting, and LLM-friendly formatted output including links to the original images.

## MCP Tools

### `browse_document`

View full page transcriptions by reference code. Returns original text (usually Swedish), links to bildvisaren (image viewer), and ALTO XML.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reference_code` | str | *(required)* | Document reference code (e.g., `SE/RA/420422/01`) |
| `pages` | str | *(required)* | Page spec: single (`"5"`), range (`"1-10"`), or list (`"5,7,9"`) |
| `highlight_term` | str \| None | None | Keyword to highlight in transcriptions |
| `max_pages` | int | 20 | Maximum pages to retrieve (max 20) |
| `dedup` | bool | True | Session deduplication (re-browsed pages become stubs) |
| `research_context` | str \| None | None | Research goal (telemetry) |

**Token cost**: ~300 tokens overhead + ~200-1500 per page depending on content density. Dense court protocol pages average ~1000 tokens; cover pages ~300.

## Components

- **tools.py**: FastMCP server setup and LLM instructions
- **browse_tool.py**: Tool registration, input validation, and dedup logic
- **formatter.py**: `PlainTextFormatter` — formats browse results for LLM consumption

## Standalone Usage

```bash
# stdio transport
python -m ra_mcp_browse_mcp.server

# HTTP transport
python -m ra_mcp_browse_mcp.server --port 3002
```

## Dependencies

- Internal: `ra-mcp-browse`
- External: `fastmcp`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with namespace `browse`. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

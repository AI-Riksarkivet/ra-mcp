# ra-mcp-guide-mcp

MCP resources for Riksarkivet historical guides and documentation.

## Overview

Serves historical documentation about Swedish archives as MCP resources. The guides cover topics like courts (*Domstolar*), prisons (*Fängelse*), taxation (*Skatt*), church records (*Statskyrkan*), and many more — 50+ sections loaded from markdown files at startup.

## MCP Resources

### `riksarkivet://contents/table_of_contents`

Returns the complete guide index (*Innehållsförteckning*) listing all available sections.

### `riksarkivet://guide/{filename}`

Returns the content of a specific guide section by filename.

**Available sections** (partial list):

| Filename | Topic |
|----------|-------|
| `01_Domstolar.md` | Courts |
| `02_Fangelse.md` | Prisons |
| `03_Skatt.md` | Taxation |
| `04_Stadens_Forvaltning.md` | City administration |
| `05_Lan.md` | Counties |
| `06_Statskyrkan.md` | State church |
| `07_Folkbokforing.md` | Population registration |
| `24_Polis.md` | Police |
| `46-61_Forsvaret.md` | Military/defense |

Use the table of contents resource to discover all available sections.

## Components

- **tools.py**: FastMCP server with resource registration. Loads markdown files from `resources/` directory (resolved via package path or working directory).

## Standalone Usage

```bash
# stdio transport
python -m ra_mcp_guide_mcp.server

# HTTP transport
python -m ra_mcp_guide_mcp.server --port 3003
```

## Dependencies

- Internal: `ra-mcp-common`
- External: `fastmcp`

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()` with namespace `guide`. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

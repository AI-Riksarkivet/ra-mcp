# ra-mcp-guide-mcp

MCP resources for Riksarkivet historical guides and documentation.

## MCP Resources

- `riksarkivet://contents/table_of_contents` — Complete guide index
- `riksarkivet://guide/{filename}` — Individual guide sections (e.g., `01_Domstolar.md`)

## Components

- **mcp.py**: FastMCP server with resource registration, loads markdown files from `resources/`

## Dependencies

- `ra-mcp-common`: Shared utilities
- `fastmcp`: MCP server framework

## Part of ra-mcp

Imported by the root server via `FastMCP.import_server()`.

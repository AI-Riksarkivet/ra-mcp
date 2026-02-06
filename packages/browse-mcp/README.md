# ra-mcp-browse-mcp

MCP tool for browsing Riksarkivet document pages.

## MCP Tools

- **browse_document**: View full page transcriptions by reference code, with optional search term highlighting

## Components

- **mcp.py**: FastMCP server setup and LLM instructions
- **browse_tool.py**: Tool registration and implementation
- **formatter.py**: Browse result formatting for LLM output

## Dependencies

- `ra-mcp-browse`: Browse domain logic and API clients
- `fastmcp`: MCP server framework

## Part of ra-mcp

Imported by the root server via `FastMCP.import_server()`.

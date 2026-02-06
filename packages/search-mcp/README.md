# ra-mcp-search-mcp

MCP tools for searching Riksarkivet transcribed documents.

## MCP Tools

- **search_transcribed**: Search AI-transcribed text in digitised documents with advanced Solr query syntax
- **search_metadata**: Search document metadata (titles, names, places, descriptions)

## Components

- **mcp.py**: FastMCP server setup and LLM instructions
- **search_tool.py**: Tool registration and implementation
- **formatter.py**: Search result formatting for LLM output

## Dependencies

- `ra-mcp-search`: Search domain logic
- `fastmcp`: MCP server framework

## Part of ra-mcp

Imported by the root server via `FastMCP.import_server()`.

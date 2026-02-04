# ra-mcp-server

Riksarkivet MCP server composition and CLI - provides the main MCP server that composes all tool servers and the CLI entry point.

## Installation

```bash
pip install ra-mcp-server
```

## Usage

### CLI

```bash
# Start the MCP server (stdio transport for Claude Desktop)
ra serve

# Start with HTTP/SSE transport
ra serve --port 8000

# Search and browse commands
ra search "Stockholm"
ra browse "SE/RA/420422/01" --page 5
```

### MCP Server

The server uses FastMCP composition to combine specialized tool servers:

- **Search Tools**: Search and browse transcribed historical documents
- Future tool servers can be added with appropriate prefixes

## Environment Variables

- `RA_MCP_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `RA_MCP_LOG_API`: Enable API call logging to file
- `RA_MCP_TIMEOUT`: Override default timeout in seconds

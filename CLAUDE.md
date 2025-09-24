# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## IMPORTANT

- Never write any code that you don't also test! CHECK IT!
- Prefer change file instead of creating a new one 
- Always read the whole file don't just read the head

## Commands

### Development
- **Run the main MCP server (stdio)**: `cd src/ra_mcp && python server.py`
- **Run with SSE/HTTP transport on port 8000**: `cd src/ra_mcp && python server.py --http`
- **Run with SSE transport (dev mode)**: `cd src/ra_mcp && python server.py --http`
- **Install dependencies**: `uv sync && uv pip install -e .`

### Claude Desktop Integration
To connect Claude Desktop to a running SSE server, add the following configuration:

**macOS/Linux**: `~/.config/claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json` (typically `C:\Users\[YourUsername]\AppData\Roaming\Claude\claude_desktop_config.json`)

### Claude Code Integration
To connect the MCP server to Claude Code:
1. Start the server with SSE transport: `cd src/ra_mcp && python server.py --http`
2. Add the server to Claude Code: `claude mcp add --transport sse ra-mcp http://localhost:8000/sse`
3. Verify connection: `claude mcp list`

The server tools will be available with the `mcp__ra-mcp__` prefix.


### HTR Gradio Application
- **Install HTR dependencies**: `cd htr_gradio && uv sync`
- **Run HTR Gradio app**: `cd htr_gradio && uv run python gradio_htrflow.py`

### Langflow Installation and Setup
**Prerequisites:**
- Python 3.10-3.13 (macOS/Linux) or 3.10-3.12 (Windows)
- uv package manager
- Minimum: Dual-core CPU, 2 GB RAM
- Recommended: Multi-core CPU, 4+ GB RAM

**Installation:**
1. Create and activate virtual environment with uv
2. Install Langflow: `uv pip install langflow`
3. Install specific version (optional): `uv pip install langflow==1.4.22`
4. Start Langflow: `uv run langflow run`
5. Access at http://127.0.0.1:7860

### Claude Code as MCP Server
**Start Claude Code as MCP server:**
```bash
claude mcp serve
```

**Configure Claude Desktop to use Claude Code as MCP server:**
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "claude-code": {
      "command": "claude",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

### Building and Publishing with Dagger
The project uses Dagger for containerized builds and publishing.

**Build locally:**
```bash
dagger call build
```

**Build and publish to Docker registry:**
```bash
dagger call publish \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="latest" \
  --source=.
```

**Available Dagger functions:**
- `build`: Creates a production-ready container image
- `test`: Runs the test suite using the built container
- `publish`: Builds and publishes container image to registry with authentication
- `build-local`: Build with custom environment variables and settings

**Prerequisites for publishing:**
- Set `DOCKER_USERNAME` environment variable with Docker registry username
- Set `DOCKER_PASSWORD` environment variable with Docker registry password
- Ensure Docker registry access for the specified credentials

## Architecture

### MCP Server Structure
The project implements a FastMCP-based Model Context Protocol server that provides access to Swedish National Archives (Riksarkivet) data through multiple mounted sub-servers:

- **Main Server** (`src/ra_mcp/server.py`): The entry point for the Riksarkivet MCP server
  - **RA Tools** (`tools.py`): Core functionality for searching transcribed documents, browsing documents, and getting document structure
  - **RA Core** (`ra_core.py`): Core API client for Riksarkivet services
  - **Cache** (`cache.py`): Caching functionality for API responses

### Core Components
Located in `src/ra_mcp/`:
- **RA Core** (`ra_core.py`): Main API client for accessing Riksarkivet's transcribed documents
- **Tools** (`tools.py`): MCP tool definitions for search_transcribed, browse_document, and get_document_structure
- **Formatters** (`formatters.py`): Text formatting utilities for search results and document content
- **Cache** (`cache.py`): Response caching to improve performance

### Typical Workflow
1. Use search_transcribed() to find documents containing keywords
2. Review search results to identify relevant reference codes and page numbers
3. Use browse_document() to view full transcriptions of specific pages
4. Use get_document_structure() to understand document organization and available manifests

### HTR Gradio Integration
The `htr_gradio/` directory contains:
- Gradio-based HTR flow client (`gradio_htrflow.py`)
- MCP client implementations (`client.py`, `client_new.py`)
- Visualization tools (`visualizer.py`)
- Simple MCP server example (`simple_mcp_server.py`)

## API Endpoints
- **Search API**: `https://data-acc.riksarkivet.se/api/records`
- **IIIF Base**: `https://data-acc.riksarkivet.se/iiif/`
- **HTRflow Space**: `https://huggingface.co/spaces/Gabriel/htrflow_mcp`

## Key Features
- Search records with transcribed text across Riksarkivet collections
- Access IIIF manifests and images with custom parameters
- Download individual or batch images from collections
- Build custom IIIF Image URLs with size and quality parameters
- Integration with HTRflow for handwritten text recognition

## MCP Specification Reference
For detailed information about the Model Context Protocol specification, implementation details, or when clarification is needed about MCP-specific features, refer to the official MCP specification documentation:
- **MCP Specification**: https://modelcontextprotocol.io/specification/2025-06-18
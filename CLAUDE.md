# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ra-mcp** (Riksarkivet Model Context Protocol) is an MCP server that provides access to transcribed historical documents from the Swedish National Archives (Riksarkivet).

### Architecture

The project is organized as a **uv workspace** with three modular packages:

```
ra-mcp/
├── packages/
│   ├── core/           # ra-mcp-core: Models, config, clients, formatters, utils
│   ├── search/         # ra-mcp-search: MCP tools, services, CLI commands
│   └── server/         # ra-mcp-server: Server composition, main CLI
├── pyproject.toml      # Workspace configuration
└── uv.lock            # Shared lockfile
```

### Package Structure

**ra-mcp-core** (no internal dependencies):
- [config.py](packages/core/src/ra_mcp_core/config.py): API URLs and configuration constants
- [models.py](packages/core/src/ra_mcp_core/models.py): Pydantic data models (SearchHit, SearchResult, BrowseResult)
- [clients/](packages/core/src/ra_mcp_core/clients/): API clients (SearchAPI, ALTOClient, OAIPMHClient, IIIFClient)
- [formatters/](packages/core/src/ra_mcp_core/formatters/): Output formatters (PlainTextFormatter, RichConsoleFormatter)
- [utils/](packages/core/src/ra_mcp_core/utils/): HTTP client, page utilities, URL generation

**ra-mcp-search** (depends on core):
- [mcp.py](packages/search/src/ra_mcp_search/mcp.py): MCP tools (`search_transcribed`, `browse_document`) and resources
- [services/](packages/search/src/ra_mcp_search/services/): Business logic (SearchOperations, BrowseOperations, display services)
- [cli/](packages/search/src/ra_mcp_search/cli/): CLI commands for search and browse

**ra-mcp-server** (depends on search):
- [server.py](packages/server/src/ra_mcp_server/server.py): FastMCP composition server
- [cli/app.py](packages/server/src/ra_mcp_server/cli/app.py): Main CLI entry point with serve command

### Package Dependencies

```
ra-mcp-core          (no internal deps)
       ↑
ra-mcp-search        (depends on core)
       ↑
ra-mcp-server        (depends on search, composes MCP servers)
```

## Development Workflow

### Setup

```bash
# Clone repository
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp

# Install dependencies (syncs workspace packages)
uv sync
```

### Running the Server

```bash
# MCP server (stdio) - for Claude Desktop integration
uv run ra serve

# MCP server (HTTP/SSE) - for web clients, testing, and development
uv run ra serve --port 8000

# With verbose logging
uv run ra serve --port 8000 --log
```

### Using the CLI

The project includes a full-featured CLI for searching and browsing documents:

```bash
# Search for documents
uv run ra search "trolldom"
uv run ra search "Stockholm" --max 50

# Browse specific documents
uv run ra browse "SE/RA/310187/1" --page "7,8,52"
uv run ra browse "SE/RA/420422/01" --pages "1-10" --search-term "Stockholm"

# Get help
uv run ra --help
uv run ra search --help
uv run ra browse --help
```

### Testing

**IMPORTANT**: The test infrastructure is currently being set up. Tests will be added in the `packages/*/tests/` directories.

```bash
# Run all tests (when tests exist)
uv run pytest

# Run with coverage
uv run pytest --cov=ra_mcp_core --cov=ra_mcp_search --cov=ra_mcp_server --cov-report=html

# Run specific package tests
uv run pytest packages/core/tests/ -v
uv run pytest packages/search/tests/ -v
```

**Note**: The Dagger pipeline currently skips tests until the test suite is implemented. See [.dagger/publish.go:12-16](.dagger/publish.go).

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint and auto-fix issues
uv run ruff check --fix .

# Type check (ty is configured in pyproject.toml)
uv run ty check
```

### Running CI Checks Locally

**IMPORTANT**: Before committing code, always run CI checks locally to catch issues early.

```bash
# Run full CI pipeline (same as GitHub Actions)
dagger call checks && dagger call test

# Quick check: Run code quality checks only
dagger call checks

# Quick check: Run tests only
dagger call test
```

**Best Practice**: Run `dagger call checks` before every commit to ensure:
- Code is properly formatted
- No linting errors
- Type checking passes
- Tests pass (when implemented)

This matches exactly what runs in GitHub Actions CI, preventing failed builds.

### Debugging

```bash
# Test MCP server with MCP Inspector
npx @modelcontextprotocol/inspector uv run ra serve

# Test HTTP/SSE server with curl
uv run ra serve --port 8000
curl http://localhost:8000/mcp
```

### Testing with Dagger

You can build and test the containerized server using Dagger:

```bash
# Build and test server with automatic health check
dagger call test-server --source=.

# Just build the container
dagger call build --source=.

# Start server as a Dagger service (for testing with other containers)
dagger call serve --source=. --port=7860

# Expose server on host for manual testing
dagger call serve-up --source=. --port=7860 up
```

**Interactive testing with Dagger shell:**
```bash
# Build and get a shell in the container
dagger call build --source=. terminal

# Inside the container, you can:
# - Test the server: ra serve --host 0.0.0.0 --port 7860
# - Run CLI commands: ra search "trolldom"
# - Check environment: python --version
# - Debug issues: ls -la /app
```

## Building and Publishing

### Prerequisites

The project uses [Dagger](https://docs.dagger.io/install) for containerized builds and publishing.

**For Docker publishing:**
```bash
export DOCKER_USERNAME="your-dockerhub-username"
export DOCKER_PASSWORD="your-dockerhub-token-or-password"
```

**For PyPI publishing:**
```bash
export PYPI_TOKEN="your-pypi-token"
```

### Build Commands

```bash
# Build container image locally (default: Alpine)
dagger call build --source=.

# Build with specific base image
dagger call build --source=. --base-image="python:3.12-alpine"
dagger call build --source=. --base-image="cgr.dev/chainguard/python:latest-dev"
dagger call build --source=. --base-image="python:3.12-slim"

# Run tests (currently skipped until test suite exists)
dagger call test --source=.

# Build with custom settings
dagger call build-local \
  --source=. \
  --image-repository="riksarkivet/ra-mcp" \
  --base-image="python:3.12-alpine"
```

### Publishing to Docker Registry

The project supports multiple base images for different use cases:

**Supported Base Images:**
- `python:3.12-alpine` - Lightweight Alpine Linux (default)
- `cgr.dev/chainguard/python:latest-dev` - Wolfi-based Chainguard image (minimal CVEs)
- `cgr.dev/chainguard/python:latest` - Chainguard production image
- `python:3.12-slim` - Debian slim variant
- Any Python 3.12+ image with pip support

**Publishing Examples:**

```bash
# Publish Alpine variant with explicit tag
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.3.0" \
  --base-image="python:3.12-alpine" \
  --tag-suffix="-alpine" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.3.0-alpine

# Publish Wolfi/Chainguard variant
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.3.0" \
  --base-image="cgr.dev/chainguard/python:latest-dev" \
  --tag-suffix="-wolfi" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.3.0-wolfi

# Publish Debian slim variant
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.3.0" \
  --base-image="python:3.12-slim" \
  --tag-suffix="-slim" \
  --source=.
# Result: riksarkivet/ra-mcp:v0.3.0-slim

# Auto-tag from pyproject.toml version (prefixes with "v")
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --base-image="python:3.12-alpine" \
  --tag-suffix="-alpine" \
  --source=.
```

**GitHub Actions Publishing:**

When you create a GitHub release, the workflow automatically publishes:
1. **Alpine variant**: `riksarkivet/ra-mcp:v0.3.0-alpine` (and PyPI packages)
2. **Wolfi variant**: `riksarkivet/ra-mcp:v0.3.0-wolfi`

Add more variants by editing [.github/workflows/publish.yml](.github/workflows/publish.yml).

### Publishing to PyPI

```bash
# Build and publish to PyPI
dagger call publish-pypi \
  --pypi-token=env:PYPI_TOKEN \
  --source=.
```

## Claude Code Integration

### Add MCP Server to Claude Code

```bash
# HTTP/SSE transport (recommended for development)
claude mcp add --transport sse ra-mcp http://localhost:8000/sse

# Verify connection
claude mcp list
```

### Claude Desktop Integration

Add to `claude_desktop_config.json`:

**macOS/Linux**: `~/.config/claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ra-mcp": {
      "command": "uv",
      "args": ["run", "ra", "serve"],
      "env": {}
    }
  }
}
```

## Coding Guidelines

### Core Principles

1. **Test-First Development**: Never write code without testing it! Always verify your changes work.
2. **Modify Over Create**: Prefer editing existing files over creating new ones.
3. **Read Completely**: Always read whole files, don't just read the head.
4. **Multiple Recommendations**: When possible, provide 2-3 alternative solutions.

### Documentation Standards

**When to use docstrings:**
- Public APIs and MCP tools
- Complex business logic
- Non-obvious behavior or algorithms
- Functions with important pre/post-conditions

**When to use better naming instead:**
- Simple, obvious functions
- Well-known patterns
- Standard operations

## API Endpoints

### Current Integrations
- **Search API**: `https://data.riksarkivet.se/api/records` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/Search-API)
- **IIIF Collections**: `https://lbiiif.riksarkivet.se/collection/arkiv` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/IIIF)
- **IIIF Images**: `https://lbiiif.riksarkivet.se`
- **ALTO XML**: `https://sok.riksarkivet.se/dokument/alto`
- **Bildvisning**: `https://sok.riksarkivet.se/bildvisning` (Interactive viewer)
- **OAI-PMH**: `https://oai-pmh.riksarkivet.se/OAI` - [Documentation](https://github.com/Riksarkivet/dataplattform/wiki/OAI-PMH)

### Additional Resources
- **[Riksarkivet Data Platform Wiki](https://github.com/Riksarkivet/dataplattform/wiki)**: Comprehensive API documentation
- **[Förvaltningshistorik](https://forvaltningshistorik.riksarkivet.se/Index.htm)**: Semantic search interface (experimental)
- **[HTRflow](https://pypi.org/project/htrflow/)**: Handwritten text recognition pipeline (PyPI package)


## Common Tasks

### Adding a New MCP Tool

1. Edit [mcp.py](packages/search/src/ra_mcp_search/mcp.py) or create a new tool file in the search package
2. Use `@search_mcp.tool()` decorator with comprehensive description
3. Add detailed docstring with examples and parameter documentation
4. If creating a new MCP module, import it in [server.py](packages/server/src/ra_mcp_server/server.py):

```python
# In server.py
from ra_mcp_new_module.mcp import new_mcp

async def setup_server():
    await main_server.import_server(search_mcp)
    await main_server.import_server(new_mcp, prefix="prefix")  # Optional prefix
```

### Adding a New MCP Resource

Resources provide static or dynamic content to MCP clients:

```python
@search_mcp.resource("riksarkivet://my-resource/{param}")
def get_my_resource(param: str) -> str:
    """
    Description of what this resource provides.

    Args:
        param: Parameter description

    Returns:
        Resource content as string
    """
    return f"Content for {param}"
```

### Adding API Clients

1. Create new client in [packages/core/src/ra_mcp_core/clients/](packages/core/src/ra_mcp_core/clients/)
2. Follow existing patterns (see [alto_client.py](packages/core/src/ra_mcp_core/clients/alto_client.py))
3. Use the centralized HTTPClient from utils
4. Add comprehensive error handling
5. Use dependency injection for HTTP client

### Adding a New Package/Module

To add a new MCP module (e.g., `ra-mcp-metadata`):

1. Create the package structure:
   ```bash
   mkdir -p packages/metadata/src/ra_mcp_metadata/{services,cli}
   mkdir -p packages/metadata/tests
   ```

2. Create `packages/metadata/pyproject.toml`:
   ```toml
   [project]
   name = "ra-mcp-metadata"
   version = "0.2.7"
   dependencies = ["ra-mcp-core"]

   [tool.uv.sources]
   ra-mcp-core = { workspace = true }

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```

3. Add MCP tools in `mcp.py`, CLI commands in `cli/`
4. Import into server's composition
5. Register CLI sub-app if needed

### Updating Dependencies

```bash
# Add new dependency to a package
cd packages/core && uv add package-name

# Add development dependency (root)
uv add --dev package-name

# Update all dependencies
uv sync --upgrade

# Update specific dependency
uv add package-name@latest
```

### Working with Git

```bash
# Check status
git status

# Stage changes
git add .

# Commit with conventional commit format
git commit -m "feat: add new search feature"
git commit -m "fix: resolve timeout issue"
git commit -m "docs: update API documentation"

# Push changes
git push
```

**Conventional Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Debugging Tips

**Environment Variables for Debugging:**
```bash
# Set logging level (DEBUG, INFO, WARNING, ERROR)
export RA_MCP_LOG_LEVEL=DEBUG

# Enable API call logging to file (ra_mcp_api.log)
export RA_MCP_LOG_API=1

# Override timeout (useful for Hugging Face)
export RA_MCP_TIMEOUT=120
```

**MCP Server Issues:**
```bash
# Use MCP Inspector for interactive testing
npx @modelcontextprotocol/inspector uv run ra serve

# Enable verbose logging with environment variable
RA_MCP_LOG_LEVEL=DEBUG uv run ra serve --port 8000

# Test HTTP endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

**Search Issues:**
```bash
# Test search directly via CLI with debug logging
RA_MCP_LOG_LEVEL=DEBUG uv run ra search "test query" --max 5

# Check API response
curl "https://data.riksarkivet.se/api/records?q=Stockholm&rows=1"

# Monitor API logs (if RA_MCP_LOG_API=1)
tail -f ra_mcp_api.log
```

**Debugging on Hugging Face:**
See [DEBUGGING.md](DEBUGGING.md) for comprehensive guide on debugging timeout and API issues when deployed to Hugging Face Spaces.

## MCP Specification Reference

For detailed information about the Model Context Protocol specification, implementation details, or when clarification is needed about MCP-specific features, refer to the official documentation:

- **[MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18)**: Official protocol specification
- **[FastMCP Documentation](https://github.com/jlowin/fastmcp)**: FastMCP library documentation

## Troubleshooting

### Common Issues

**Issue**: Server won't start
- Check if port 8000 is already in use: `lsof -i :8000`
- Try a different port: `uv run ra serve --port 8001`

**Issue**: No search results found
- Verify API is accessible: `curl https://data.riksarkivet.se/api/records`
- Check search syntax (use exact terms first, then wildcards)
- Try broader search terms

**Issue**: Import errors
- Reinstall dependencies: `uv sync --reinstall`
- Check Python version: `python --version` (requires 3.12+)

**Issue**: Tests not running
- Test infrastructure is being set up - see [Testing](#testing) section
- Dagger currently skips tests in publish pipeline

### Getting Help

```bash
# General help
uv run ra --help

# Command-specific help
uv run ra serve --help
uv run ra search --help
uv run ra browse --help

# Check version
uv run ra --version
```

## Notes for Claude Code

When working with this codebase:

1. **Always test changes**: Run the server or CLI to verify functionality
2. **Read full context**: Use the Read tool on complete files, not just snippets
3. **Prefer modifications**: Edit existing code rather than creating new files
4. **Check types**: The project uses type hints - maintain them in all code
5. **Follow patterns**: Match existing code style and patterns (see [packages/search/src/ra_mcp_search/services/](packages/search/src/ra_mcp_search/services/))
6. **Document thoroughly**: MCP tools need excellent documentation for LLM understanding
7. **Workspace awareness**: Changes to core affect both search and server packages

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ra-mcp** (Riksarkivet Model Context Protocol) is an MCP server that provides access to transcribed historical documents from the Swedish National Archives (Riksarkivet).

### Architecture

The project uses FastMCP's composition pattern to combine multiple specialized servers:

- **Main Server** ([server.py](src/ra_mcp/server.py)): FastMCP composition server that imports tool servers
- **Search Tools** ([search_tools.py](src/ra_mcp/search_tools.py)): MCP tools (`search_transcribed`, `browse_document`) and resources
- **CLI** ([cli/](src/ra_mcp/cli/)): Command-line interface using Typer
- **Services** ([services/](src/ra_mcp/services/)): Business logic (SearchOperations, BrowseOperations, Display services)
- **Clients** ([clients/](src/ra_mcp/clients/)): API clients for IIIF, ALTO, OAI-PMH, and Search APIs
- **Formatters** ([formatters/](src/ra_mcp/formatters/)): Output formatting (Plain text, Rich console)
- **Utils** ([utils/](src/ra_mcp/utils/)): HTTP client, page utilities, URL generation

## Development Workflow

### Setup

```bash
# Clone repository
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp

# Install dependencies
uv sync && uv pip install -e .
```

### Running the Server

```bash
# MCP server (stdio) - for Claude Desktop integration
uv run ra serve

# MCP server (HTTP/SSE) - for web clients, testing, and development
uv run ra serve --http --port 8000

# With verbose logging
uv run ra serve --http --verbose
```

### Using the CLI

The project includes a full-featured CLI for searching and browsing documents:

```bash
# Search for documents
uv run ra search "trolldom"
uv run ra search "Stockholm" --max 50

# Browse specific documents
uv run ra browse "SE/RA/310187/1" --pages "7,8,52"
uv run ra browse "SE/RA/420422/01" --pages "1-10" --search-term "Stockholm"

# Get help
uv run ra --help
uv run ra search --help
uv run ra browse --help
```

### Testing

**IMPORTANT**: The test infrastructure is currently being set up. Tests will be added in the `tests/` directory.

```bash
# Run all tests (when tests exist)
uv run pytest

# Run with coverage
uv run pytest --cov=ra_mcp --cov-report=html

# Run specific test file
uv run pytest tests/test_search.py -v

# Run specific test
uv run pytest tests/test_search.py::test_search_transcribed -v
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

### Debugging

```bash
# Test MCP server with MCP Inspector
npx @modelcontextprotocol/inspector uv run ra serve

# Test HTTP/SSE server with curl
uv run ra serve --http
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
# Build container image locally
dagger call build

# Run tests (currently skipped until test suite exists)
dagger call test

# Build with custom settings
dagger call build-local
```

### Security Scanning

The project includes Trivy vulnerability scanning for container images:

```bash
# Scan for CRITICAL and HIGH vulnerabilities (fails if found)
dagger call scan --source=.

# Scan with custom severity levels
dagger call scan --source=. --severity="CRITICAL,HIGH,MEDIUM"

# Scan without failing the build (for reports)
dagger call scan --source=. --exit-code=0

# Get JSON output for automation
dagger call scan-json --source=.

# CI/CD scan (fails on CRITICAL/HIGH)
dagger call scan-ci --source=.

# Generate SARIF report for GitHub Security tab
dagger call scan-sarif --source=. --output-path="trivy-results.sarif"
```

**Current Scan Results Summary:**
- **Debian packages**: 2 HIGH (glibc CVE-2026-0861 - no fix available)
- **Python packages**: 0 HIGH (all fixed!)
- **Total**: 2 HIGH, 0 CRITICAL ✅

**Recent CVE Fixes:**
- ✅ Fixed urllib3 CVEs by upgrading to 2.6.3
- ✅ Fixed python-multipart CVE-2026-24486 by upgrading to 0.0.22
- ✅ Optimized Dockerfile with pinned uv version (0.5.13)
- ✅ Using python:3.12-slim-trixie (Debian 13) for latest security patches

**Note on Base Image Choice:**
- Tested distroless (Debian 12): 6 CRITICAL + 13 HIGH vulnerabilities
- Using slim-trixie (Debian 13): 0 CRITICAL + 2 HIGH vulnerabilities
- Debian 13 is significantly more secure than Debian 12 for this use case

### Publishing to Docker Registry

```bash
# Publish with explicit tag
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.2.0" \
  --source=.

# Auto-tag from pyproject.toml version (prefixes with "v")
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --source=.
```

**Important Notes:**
- Tests run automatically before publishing (currently skipped)
- Both `DOCKER_USERNAME` and `DOCKER_PASSWORD` must be set
- Use `env:` prefix for Secret parameters
- Pre-built images available at [Docker Hub](https://hub.docker.com/r/riksarkivet/ra-mcp)

### Publishing to PyPI

```bash
# Build and publish to PyPI
dagger call publish-pypi \
  --pypi-token=env:PYPI_TOKEN \
  --source=.
```

**Note**: PyPI publish runs tests first. Deployment is aborted if tests fail.

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

### Claude Code as MCP Server

You can also run Claude Code itself as an MCP server:

```bash
# Start Claude Code as MCP server
claude mcp serve
```

Then add to `claude_desktop_config.json`:
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

1. Edit [search_tools.py](src/ra_mcp/search_tools.py) or create a new tool file
2. Use `@search_mcp.tool()` decorator with comprehensive description
3. Add detailed docstring with examples and parameter documentation
4. If creating a new file, import in [server.py](src/ra_mcp/server.py):

```python
# In server.py
from ra_mcp.new_tools import new_mcp

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

1. Create new client in [clients/](src/ra_mcp/clients/)
2. Follow existing patterns (see [alto_client.py](src/ra_mcp/clients/alto_client.py))
3. Use `httpx` for HTTP requests
4. Add comprehensive error handling
5. Use dependency injection for HTTP client

### Updating Dependencies

```bash
# Add new dependency
uv add package-name

# Add development dependency
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
RA_MCP_LOG_LEVEL=DEBUG uv run ra serve --http

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
- Try a different port: `uv run ra serve --http --port 8001`

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
5. **Follow patterns**: Match existing code style and patterns (see [services/](src/ra_mcp/services/))
6. **Document thoroughly**: MCP tools need excellent documentation for LLM understanding

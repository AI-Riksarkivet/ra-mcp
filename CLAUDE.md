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

**Example:**
```python
# ❌ Bad - unclear names requiring comments
def p(d):  # Process data
    r = d * 2  # Double the result
    return r

# ✅ Good - self-documenting code
def double_search_results(search_data: SearchResult) -> ProcessedResult:
    """
    Double the search result count for pagination estimation.

    Used when search API returns partial results and we need to estimate
    total available documents for pagination display.
    """
    return search_data.scale_by_factor(2)

# ✅ Also good - simple operation, no docstring needed
def is_valid_page_number(page: int) -> bool:
    return page > 0 and page < 10000
```

**Critical line-specific notes**: Use docstrings to explain important context, NOT inline comments.

```python
# ❌ Avoid inline comments
def fetch_document(ref_code: str):
    # IMPORTANT: Must use httpx due to Riksarkivet timeout bug
    client = httpx.Client()

# ✅ Better - document in function/module docstring
def fetch_document(ref_code: str):
    """
    Fetch document from Riksarkivet API.

    Note: Uses httpx instead of requests due to timeout issues with
    Riksarkivet's API servers. See: https://github.com/AI-Riksarkivet/ra-mcp/issues/X
    """
    client = httpx.Client()
```

### API Client Choice

**IMPORTANT**: When using Riksarkivet endpoints, prefer `httpx` or `urllib` instead of `requests`. There is a timeout bug when using the `requests` library against Riksarkivet's APIs.

```python
# ✅ Preferred
import httpx
response = httpx.get("https://data.riksarkivet.se/api/records")

# ❌ Avoid - has timeout issues
import requests
response = requests.get("https://data.riksarkivet.se/api/records")
```

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

## Project Structure

```
ra-mcp/
├── src/ra_mcp/
│   ├── server.py              # Main MCP server (FastMCP composition)
│   ├── search_tools.py        # MCP tools and resources
│   ├── config.py              # Configuration
│   ├── models.py              # Data models
│   ├── cli/                   # CLI commands (Typer)
│   │   ├── cli.py
│   │   ├── commands.py
│   │   └── cli_progress.py
│   ├── services/              # Business logic layer
│   │   ├── search_operations.py
│   │   ├── browse_operations.py
│   │   ├── search_display_service.py
│   │   └── browse_display_service.py
│   ├── clients/               # API clients
│   │   ├── search_client.py
│   │   ├── alto_client.py
│   │   ├── iiif_client.py
│   │   └── oai_pmh_client.py
│   ├── formatters/            # Output formatting
│   │   ├── base_formatter.py
│   │   ├── plain_formatter.py
│   │   └── rich_formatter.py
│   └── utils/                 # Utilities
│       ├── http_client.py
│       ├── page_utils.py
│       └── url_generator.py
├── resources/                 # Historical guide markdown files
├── tests/                     # Test suite (TO BE CREATED)
├── .dagger/                   # CI/CD pipeline (Dagger)
│   ├── main.go
│   └── publish.go
├── .github/workflows/         # GitHub Actions
├── pyproject.toml             # Python project configuration
├── Dockerfile                 # Container image
└── CLAUDE.md                  # This file
```

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

**MCP Server Issues:**
```bash
# Use MCP Inspector for interactive testing
npx @modelcontextprotocol/inspector uv run ra serve

# Enable verbose logging
uv run ra serve --verbose

# Test HTTP endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

**Search Issues:**
```bash
# Test search directly via CLI
uv run ra search "test query" --max 5

# Check API response
curl "https://data.riksarkivet.se/api/records?q=Stockholm&rows=1"
```

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

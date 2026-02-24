---
icon: lucide/code
---

# Development

Guide for setting up, contributing to, and deploying ra-mcp.

---

## Setup

```bash
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp
uv sync
```

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

## Running the Server

```bash
# MCP server (stdio) — for Claude Desktop integration
uv run ra serve

# MCP server (HTTP) — for web clients, testing, and development
uv run ra serve --port 7860

# With verbose logging
uv run ra serve --port 7860 -v

# Selective modules
uv run ra serve --port 7860 --modules search,browse
```

## Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run ra serve
```

## Testing

```bash
# Run all tests
uv run pytest

# Run specific package tests
uv run pytest packages/common/tests/ -v
uv run pytest packages/search/tests/ -v
uv run pytest packages/browse/tests/ -v

# Run with coverage
uv run pytest --cov=ra_mcp_common --cov=ra_mcp_search --cov=ra_mcp_browse --cov-report=html
```

### Testing Principles

- One test file per source module: `test_formatting.py` tests `formatting.py`
- Flat module-level functions — no test classes
- Parametrize for edge cases (pydantic pattern)
- Mock at the right boundary: inject a mock `HTTPClient` via constructor for domain packages, use `Client(mcp)` for MCP tools
- Test behavior, not instrumentation

## Code Quality

```bash
# Format code
uv run ruff format .

# Lint and auto-fix
uv run ruff check --fix .

# Type check
uv run ty check
```

## CI Checks

Run the same checks as GitHub Actions locally:

```bash
# Full pipeline
dagger call checks && dagger call test

# Or via Makefile
make check
```

Always run `dagger call checks` before committing.

## Environment Variables

### Debugging

| Variable | Default | Description |
|----------|---------|-------------|
| `RA_MCP_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `RA_MCP_LOG_API` | *(unset)* | Enable API logging to `ra_mcp_api.log` |
| `RA_MCP_TIMEOUT` | `60` | Override default HTTP timeout in seconds |

### HTR

| Variable | Default | Description |
|----------|---------|-------------|
| `HTR_SPACE_URL` | `https://riksarkivet-htr-demo.hf.space` | Gradio Space URL |
| `HTR_TIMEOUT` | `300` | Transcription timeout in seconds |

## Adding a New MCP Tool

1. Create a tool file in the appropriate MCP package (e.g., `packages/search-mcp/src/ra_mcp_search_mcp/`)
2. Define a `register_*_tool(mcp)` function using `@mcp.tool()`
3. Add parameter documentation via `Annotated[type, Field(description=...)]`
4. Call the register function from the package's `tools.py`
5. Add tests using `Client(mcp)` for in-process testing

## Adding a New Module

1. Create domain package: `packages/mymodule/` with models, clients, operations
2. Create MCP package: `packages/mymodule-mcp/` with tool registration
3. Register in `src/ra_mcp_server/server.py` `AVAILABLE_MODULES`:

```python
AVAILABLE_MODULES = {
    "mymodule": {
        "server": mymodule_mcp,
        "description": "Description for --list-modules",
        "default": True,
    },
}
```

4. Add dependencies to root `pyproject.toml`

## Adding a New Skill

1. Create `plugins/ra-mcp-tools/skills/{name}/SKILL.md`
2. Add YAML frontmatter with `name` and `description`
3. The skill is auto-discovered on server restart

## Updating Dependencies

```bash
# Add to a package
cd packages/common && uv add package-name

# Add dev dependency (root)
uv add --dev package-name

# Sync all
uv sync
```


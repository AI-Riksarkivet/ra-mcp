---
name: add-mcp-package
description: "Scaffold a new MCP workspace package under packages/. Covers directory structure, pyproject.toml, tools.py, server.py, tool registration, formatter, __init__.py, tests, root server wiring, and uv sync. Use when: add new MCP package, new workspace, new tool server, scaffold package, add module."
---

# Add a New MCP Workspace Package

Step-by-step guide to adding a new `ra-mcp-<name>-mcp` package to the workspace.

## Prerequisites

Decide on your package name. Convention: `<name>-mcp` directory, `ra-mcp-<name>-mcp`
PyPI name, `ra_mcp_<name>_mcp` Python import.

Example mapping for a package called **viewer**:

| Slot | Value |
|------|-------|
| Directory | `packages/viewer-mcp/` |
| PyPI name | `ra-mcp-viewer-mcp` |
| Python package | `ra_mcp_viewer_mcp` |
| FastMCP instance | `viewer_mcp` |
| Server namespace | `"viewer"` |

## Step 1 — Create directory structure

```
packages/<name>-mcp/
├── pyproject.toml
├── README.md
├── src/ra_mcp_<name>_mcp/
│   ├── __init__.py
│   ├── py.typed            # empty file, PEP 561 marker
│   ├── tools.py            # FastMCP server + instructions + tool registration
│   ├── server.py           # Standalone entry point for isolated dev/testing
│   └── formatter.py        # LLM output formatting (optional)
└── tests/
    └── test_tools.py
```

## Step 2 — `pyproject.toml`

```toml
[project]
name = "ra-mcp-<name>-mcp"
version = "0.3.0"                         # match current workspace version
description = "<one-line description>"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    # Domain package (if one exists):
    # "ra-mcp-<name>",
    "ra-mcp-common",
    "fastmcp>=3.0.0",
]
license = "Apache-2.0"

[tool.uv.sources]
# ra-mcp-<name> = { workspace = true }   # uncomment if domain pkg exists
ra-mcp-common = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ra_mcp_<name>_mcp"]
```

If the package depends on an existing domain package (e.g. `ra-mcp-browse`),
add it to `dependencies` and `[tool.uv.sources]`. If this is a standalone MCP
package (like `guide-mcp`), just depend on `ra-mcp-common` + `fastmcp`.

## Step 3 — `tools.py`

This file creates the FastMCP instance and registers all tools/resources.

```python
from fastmcp import FastMCP

<name>_mcp = FastMCP(
    name="ra-<name>-mcp",
    instructions="""
    <Detailed LLM-facing instructions>
    - What this module does
    - List of available tools
    - Usage examples
    - Important caveats
    """,
)


@<name>_mcp.tool()
async def <tool_name>(param1: str) -> str:
    """Tool description for LLM understanding."""
    ...
```

For larger packages, split tool registration into a separate `<name>_tool.py`
with a `register_<name>_tool(mcp)` function and call it from `tools.py`.

## Step 4 — `server.py`

Standalone entry point for running the package in isolation (dev/testing).
No custom log format — OTel handles that when enabled.

```python
"""Standalone server for ra-<name>-mcp.

    python -m ra_mcp_<name>_mcp.server
    python -m ra_mcp_<name>_mcp.server --stdio
"""

import argparse
import logging
import os

from .tools import <name>_mcp


logging.basicConfig(level=logging.INFO)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Riksarkivet <Name> MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run with stdio transport (default is HTTP)")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3001")), help="Port for HTTP server (default: 3001)")
    args = parser.parse_args()

    if args.stdio:
        <name>_mcp.run(transport="stdio")
    else:
        logger.info("MCP Server listening on http://localhost:%d/mcp", args.port)
        <name>_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
```

## Step 5 — `__init__.py`

```python
"""MCP tools for <description>."""

from .tools import <name>_mcp

__all__ = ["<name>_mcp"]
```

## Step 6 — `py.typed`

Create an empty file at `src/ra_mcp_<name>_mcp/py.typed`.

## Step 7 — `tests/test_tools.py`

```python
"""Tests for ra-mcp-<name>-mcp tools."""

from ra_mcp_<name>_mcp.tools import <name>_mcp


def test_<name>_mcp_has_name() -> None:
    assert <name>_mcp.name == "ra-<name>-mcp"
```

## Step 8 — `README.md`

```markdown
# ra-mcp-<name>-mcp

<One-line description>.

## MCP Tools

- **<tool_name>**: What it does

## Standalone usage

    python -m ra_mcp_<name>_mcp.server          # HTTP on port 3001
    python -m ra_mcp_<name>_mcp.server --stdio   # stdio transport

## Part of ra-mcp

Imported by the root server via `FastMCP.add_provider()`.
```

## Step 9 — Wire into root

### 9a. Root `pyproject.toml` — add dependency and source

```toml
# In [project] dependencies, add:
"ra-mcp-<name>-mcp",

# In [tool.uv.sources], add:
ra-mcp-<name>-mcp = { workspace = true }

# In [tool.ruff.lint.isort] known-first-party, add:
"ra_mcp_<name>_mcp"
```

### 9b. `src/ra_mcp_server/server.py` — register the module

Add import at the top alongside the other module imports:

```python
from ra_mcp_<name>_mcp.tools import <name>_mcp
```

Add entry to `AVAILABLE_MODULES`:

```python
"<name>": {
    "server": <name>_mcp,
    "description": "<Short description for --list-modules>",
    "default": True,  # or False if opt-in
},
```

## Step 10 — Sync and verify

```bash
# Install the new package into the workspace
uv sync

# Verify the module loads
uv run ra serve --list-modules

# Run package tests
uv run pytest packages/<name>-mcp/tests/ -v

# Test standalone
uv run python -m ra_mcp_<name>_mcp.server --port 3001

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m ra_mcp_<name>_mcp.server --stdio
```

## Checklist

- [ ] `packages/<name>-mcp/` directory with all files
- [ ] `pyproject.toml` has correct name, deps, and hatch wheel config
- [ ] `tools.py` exports a `<name>_mcp` FastMCP instance with tools registered
- [ ] `server.py` provides standalone `--stdio` / `--port` entry point
- [ ] `__init__.py` exports `<name>_mcp`
- [ ] `py.typed` marker exists
- [ ] `tests/test_tools.py` has at least a smoke test
- [ ] Root `pyproject.toml`: dependency added, source added, isort updated
- [ ] `server.py` in root: import added, `AVAILABLE_MODULES` entry added
- [ ] `uv sync` succeeds
- [ ] `uv run ra serve --list-modules` shows the new module

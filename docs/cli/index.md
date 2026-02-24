---
icon: lucide/terminal
---

# CLI Reference

The ra-mcp CLI provides terminal access to the same operations available through MCP tools.

```bash
uv pip install ra-mcp           # Server + MCP tools
uv pip install ra-mcp[cli]      # Add CLI commands (ra search, ra browse)
uv pip install ra-mcp[tui]      # Add interactive TUI (ra tui)
```

## Commands

| Command | Description |
|---------|-------------|
| [`ra search`](search.md) | Search transcribed historical documents |
| [`ra browse`](browse.md) | Browse pages by reference code |
| [`ra serve`](serve.md) | Start the MCP server |
| [`ra tui`](serve.md#ra-tui) | Interactive terminal browser |

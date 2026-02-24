# Local Installation

If you want to search and browse directly from your terminal (no AI client needed), or run your own server instance.

---

## Install the CLI

```bash
uv pip install ra-mcp
```

```bash
# Search transcribed documents
ra search "trolldom"
ra search "((Stockholm OR Goteborg) AND troll*)"

# Browse specific pages
ra browse "SE/RA/310187/1" --pages "7,8,52" --search-term "trolldom"
```

## Interactive TUI

For a full terminal browser experience:

```bash
uv pip install "ra-mcp[tui]"
```

```bash
ra tui                # Launch empty
ra tui "trolldom"     # Launch with pre-filled search
```

The TUI provides keyboard-driven search, document browsing, and page viewing. Press `?` for keybindings help.

See [CLI Reference](../cli/index.md) for full command documentation.

## Run Your Own Server

For development or private deployments:

```bash
# Clone and install
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp
uv sync

# Run MCP server on HTTP
uv run ra serve --port 7860

# Then connect to it
claude mcp add --transport http ra-mcp http://localhost:7860/mcp
```

Or with Docker:

```bash
docker run -p 7860:7860 riksarkivet/ra-mcp
```

## Test with MCP Inspector

For debugging or exploring the tools interactively:

```bash
cat > mcp.json <<'EOF'
{
  "mcpServers": {
    "ra-mcp": {
      "type": "streamable-http",
      "url": "https://riksarkivet-ra-mcp.hf.space/mcp"
    }
  }
}
EOF

npx -y @modelcontextprotocol/inspector --config ./mcp.json
```

Open `http://localhost:6274` in your browser to use the Inspector UI.

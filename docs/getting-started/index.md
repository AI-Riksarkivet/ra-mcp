---
icon: lucide/rocket
---

# Getting Started

ra-mcp is available as a hosted MCP server — no installation needed. Connect it to your favourite AI client and start searching Swedish historical archives immediately.

**Server URL:**

```
https://riksarkivet-ra-mcp.hf.space/mcp
```

---

## Connect to Claude.ai

Claude.ai supports adding MCP servers directly from the web interface.

1. Open [claude.ai](https://claude.ai) and go to a conversation
2. Click the **:material-puzzle: Integrations** icon (bottom-left of the chat input)
3. Select **Add more integrations...**
4. Choose **Add custom MCP server**
5. Enter:
    - **Name:** `ra-mcp`
    - **URL:** `https://riksarkivet-ra-mcp.hf.space/mcp`
6. Click **Add**

You should now see `ra-mcp` listed as a connected integration. Try asking:

> *"Search for trolldom in Swedish historical documents"*

## Connect to Claude Code (CLI)

Run a single command:

```bash
claude mcp add --transport http ra-mcp https://riksarkivet-ra-mcp.hf.space/mcp
```

Verify the connection:

```bash
claude mcp list
```

Then inside Claude Code, just ask naturally:

> *"Search for documents mentioning Stockholm from the 1600s"*

## Connect to Claude Desktop

Add this to your Claude Desktop configuration file:

=== "macOS / Linux"

    Edit `~/.config/claude/claude_desktop_config.json`:

    ```json
    {
      "mcpServers": {
        "ra-mcp": {
          "type": "streamable-http",
          "url": "https://riksarkivet-ra-mcp.hf.space/mcp"
        }
      }
    }
    ```

=== "Windows"

    Edit `%APPDATA%\Claude\claude_desktop_config.json`:

    ```json
    {
      "mcpServers": {
        "ra-mcp": {
          "type": "streamable-http",
          "url": "https://riksarkivet-ra-mcp.hf.space/mcp"
        }
      }
    }
    ```

Restart Claude Desktop after saving the file.

## Connect to VS Code / Cursor / Windsurf

Add to your project's `.vscode/mcp.json` (or global settings):

```json
{
  "mcpServers": {
    "ra-mcp": {
      "type": "streamable-http",
      "url": "https://riksarkivet-ra-mcp.hf.space/mcp"
    }
  }
}
```

## Connect to ChatGPT / Other MCP Clients

Any MCP-compatible client can connect using streamable HTTP:

| Setting | Value |
|---------|-------|
| **Transport** | Streamable HTTP |
| **URL** | `https://riksarkivet-ra-mcp.hf.space/mcp` |

---

## Adding Plugins

ra-mcp can be combined with other MCP servers to create a richer research environment. A common addition is **HTR transcription** — a server that can transcribe handwritten document images using AI.

### Adding the HTR Transcription Plugin

The [htrflow-mcp](https://huggingface.co/spaces/Riksarkivet/htrflow-mcp) server provides handwritten text recognition (HTR) capabilities, letting your AI assistant transcribe document images directly.

**Server URL:**

```
https://riksarkivet-htrflow-mcp.hf.space/gradio_api/mcp/sse
```

#### Claude.ai

1. Open [claude.ai](https://claude.ai) → **:material-puzzle: Integrations** → **Add more integrations...**
2. **Add custom MCP server**
3. Enter:
    - **Name:** `htrflow-mcp`
    - **URL:** `https://riksarkivet-htrflow-mcp.hf.space/gradio_api/mcp/sse`
4. Click **Add**

#### Claude Code

```bash
claude mcp add --transport sse htrflow-mcp https://riksarkivet-htrflow-mcp.hf.space/gradio_api/mcp/sse
```

#### Claude Desktop

Add alongside `ra-mcp` in your config file:

```json
{
  "mcpServers": {
    "ra-mcp": {
      "type": "streamable-http",
      "url": "https://riksarkivet-ra-mcp.hf.space/mcp"
    },
    "htrflow-mcp": {
      "url": "https://riksarkivet-htrflow-mcp.hf.space/gradio_api/mcp/sse"
    }
  }
}
```

#### VS Code / Cursor / Windsurf

Add to `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "ra-mcp": {
      "type": "streamable-http",
      "url": "https://riksarkivet-ra-mcp.hf.space/mcp"
    },
    "htrflow-mcp": {
      "url": "https://riksarkivet-htrflow-mcp.hf.space/gradio_api/mcp/sse"
    }
  }
}
```

### Using Both Servers Together

Once both servers are connected, you can combine search and transcription in a single conversation:

1. **Search** for documents using `ra-mcp`
2. **Browse** specific pages to find interesting content
3. **Transcribe** document images using `htrflow-mcp` for pages that need fresh OCR/HTR

> *"Search for trolldom in court records, then transcribe page 12 of the first result"*

---

## Install the CLI

If you want to search and browse directly from your terminal (no AI client needed):

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

## Run Your Own Server

For development or private deployments:

```bash
# Clone and install
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp
uv sync

# Run MCP server on HTTP
uv run ra serve --port 8000

# Then connect to it
claude mcp add --transport http ra-mcp http://localhost:8000/mcp
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

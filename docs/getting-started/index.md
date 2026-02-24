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


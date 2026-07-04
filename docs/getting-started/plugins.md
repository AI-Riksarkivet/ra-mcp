# Adding More MCP Servers

ra-mcp can be combined with other **MCP servers** to create a richer research environment. A common addition is **HTR transcription** — a server that can transcribe handwritten document images using AI.

!!! note "Looking for the ra-mcp *skills*?"
    The ra-mcp **skills** (research-workflow guides like `/archive-search`) are **not** MCP servers — see [Skills](../tools/skills.md) for how to get them (automatic on claude.ai, `/plugin install` on Claude Code). This page is only about connecting *additional MCP servers*.

---

## HTR Transcription Plugin

The [htrflow-mcp](https://huggingface.co/spaces/Riksarkivet/htrflow-mcp) server provides handwritten text recognition (HTR) capabilities, letting your AI assistant transcribe document images directly.

**Server URL:**

```
https://riksarkivet-htrflow-mcp.hf.space/gradio_api/mcp/sse
```

### Claude.ai

1. Open [claude.ai](https://claude.ai) → **:material-puzzle: Integrations** → **Add more integrations...**
2. **Add custom MCP server**
3. Enter:
    - **Name:** `htrflow-mcp`
    - **URL:** `https://riksarkivet-htrflow-mcp.hf.space/gradio_api/mcp/sse`
4. Click **Add**

### Claude Code

```bash
claude mcp add --transport sse htrflow-mcp https://riksarkivet-htrflow-mcp.hf.space/gradio_api/mcp/sse
```

### Claude Desktop

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

### VS Code / Cursor / Windsurf

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

---

## Using Both Servers Together

Once both servers are connected, you can combine search and transcription in a single conversation:

1. **Search** for documents using `ra-mcp`
2. **Browse** specific pages to find interesting content
3. **Transcribe** document images using `htrflow-mcp` for pages that need fresh OCR/HTR

> *"Search for trolldom in court records, then transcribe page 12 of the first result"*

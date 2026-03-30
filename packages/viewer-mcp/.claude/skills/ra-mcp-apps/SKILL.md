---
name: ra-mcp-apps
description: "MCP Apps guide: FastMCP 3.1+ server, Svelte 5 view, tool visibility, polling, sizing, fullscreen, view persistence. Use for any MCP App/UI work."
---

# MCP Apps — Quick Reference

Server (FastMCP) ↔ Host (Claude/ChatGPT) ↔ View (sandboxed iframe). The View and Server never talk directly.

## Supporting Files

- [patterns.md](patterns.md) — MCP Apps patterns: polling, chunked data, theming, fullscreen, view persistence (Brick Builder), per-view state, autoResize, command queues
- [csp-cors.md](csp-cors.md) — CSP configuration, CORS, stable origins, connectDomains vs resourceDomains
- [testing.md](testing.md) — Testing with basic-host, Claude.ai, VS Code, tunnels

## Data Flow

| Field | LLM sees? | View sees? | Use for |
|-------|-----------|------------|---------|
| `content` | Yes | Yes | Short text summary for model context |
| `structuredContent` | No* | Yes | Rich data for UI rendering |
| `_meta` | No | Yes | viewUUID, timestamps, metadata |

*ChatGPT exposes structuredContent to both.

## Tool Visibility

| Visibility | LLM? | View? | Use case |
|------------|-------|-------|----------|
| `["model", "app"]` (default) | Yes | Yes | General tools |
| `["model"]` | Yes | No | LLM-only triggers |
| `["app"]` | No | Yes | Pagination, refresh, polling, dangerous actions |

## Server Quick Start (FastMCP 3.1+)

```python
from fastmcp import FastMCP, Context
from fastmcp.server.apps import AppConfig, ResourceCSP, UI_EXTENSION_ID
from fastmcp.tools import ToolResult
from mcp import types

mcp = FastMCP("My App")
RESOURCE_URI = "ui://my-app/view.html"

# Tool with UI — creates an iframe
@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))
async def show_data(query: str, ctx: Context) -> ToolResult:
    has_ui = ctx.client_supports_extension(UI_EXTENSION_ID)
    return ToolResult(
        content=[types.TextContent(type="text", text="Summary for LLM")],
        structured_content={"data": [...], "query": query},
    )

# App-only tool — View calls this, LLM never sees it
@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]))
async def load_page(page: int) -> ToolResult: ...

# Resource — serves the bundled HTML
@mcp.resource(uri=RESOURCE_URI)
def get_ui() -> str:
    return Path("dist/mcp-app.html").read_text()
```

## View Quick Start (Svelte 5)

```svelte
<script lang="ts">
import { onMount } from "svelte";
import { App, applyDocumentTheme, applyHostStyleVariables, applyHostFonts, type McpUiHostContext } from "@modelcontextprotocol/ext-apps";

let app = $state<App | null>(null);
let hostContext = $state<McpUiHostContext | undefined>();
let data = $state.raw<MyData | null>(null);

$effect(() => {
  if (hostContext?.theme) applyDocumentTheme(hostContext.theme);
  if (hostContext?.styles?.variables) applyHostStyleVariables(hostContext.styles.variables);
  if (hostContext?.styles?.css?.fonts) applyHostFonts(hostContext.styles.css.fonts);
});

onMount(async () => {
  const instance = new App(
    { name: "My App", version: "1.0.0" },
    { availableDisplayModes: ["inline", "fullscreen"] },
    { autoResize: false },  // Required for flexible-height content — see patterns.md
  );
  instance.ontoolresult = (result) => { data = result.structuredContent; };
  instance.onhostcontextchanged = (ctx) => { hostContext = { ...hostContext, ...ctx }; };
  instance.onteardown = async () => { /* cleanup */ return {}; };
  await instance.connect();
  app = instance;
  hostContext = instance.getHostContext();
});
</script>
```

## Decision Checklist

| Question | Answer |
|----------|--------|
| What does the LLM need? | `content` |
| What does the UI need? | `structuredContent` |
| LLM triggers this? | `visibility: ["model"]` or default |
| UI-only action? | `visibility: ["app"]` |
| Data >100KB? | Chunked app-only tool — see [patterns.md](patterns.md) |
| External APIs? | Declare in `ResourceCSP` — see [csp-cors.md](csp-cors.md) |
| Fullscreen? | `availableDisplayModes: ["inline", "fullscreen"]` |
| View should persist across LLM tool calls? | Brick Builder pattern — see [patterns.md](patterns.md) |
| Multi-user server? | Per-view state with MemoryStore — see [patterns.md](patterns.md) |

## Gotchas

- **Tool with `resourceUri` = new iframe.** Never put `AppConfig(resource_uri=...)` on update tools.
- **`autoResize: false`** required for flexible-height content to prevent infinite resize loops.
- **`onteardown`** — always implement to stop polling and clean up.
- **CSP deny-by-default.** External images silently don't load without `resource_domains`.
- **`asyncio.gather`** for parallel fetches — sequential `await` calls wait for each other.
- **Multi-user servers** need per-view state (MemoryStore + view_id), not module-level globals.

# MCP Apps Patterns

Official patterns from the ext-apps SDK. Source: https://github.com/modelcontextprotocol/ext-apps

## Tools that are private to Apps

Set `visibility` to `["app"]` to make tools only callable by Apps (hidden from the model).

```ts
registerAppTool(server, "update-quantity", {
  inputSchema: { itemId: z.string(), quantity: z.number() },
  _meta: { ui: { resourceUri: "ui://shop/cart.html", visibility: ["app"] } },
}, async ({ itemId, quantity }) => {
  const cart = await updateCartItem(itemId, quantity);
  return { content: [{ type: "text", text: JSON.stringify(cart) }] };
});
```

## Polling for live data

App-only tool polled at regular intervals. Clean up on teardown.

```ts
let intervalId: number | null = null;

async function poll() {
  const result = await app.callServerTool({ name: "poll-data", arguments: {} });
  updateUI(result.structuredContent);
}

function startPolling() {
  if (intervalId !== null) return;
  poll();
  intervalId = window.setInterval(poll, 2000);
}

function stopPolling() {
  if (intervalId === null) return;
  clearInterval(intervalId);
  intervalId = null;
}

app.onteardown = async () => { stopPolling(); return {}; };
```

## Chunked binary transfer

Two tools: model-visible returns metadata, app-only streams chunks.

Server:
```ts
registerAppTool(server, "read_data_bytes", {
  inputSchema: { id: z.string(), offset: z.number().default(0), byteCount: z.number().default(500*1024) },
  _meta: { ui: { visibility: ["app"] } },
}, async ({ id, offset, byteCount }) => {
  const data = await loadData(id);
  const chunk = data.slice(offset, offset + byteCount);
  return {
    content: [{ type: "text", text: `${chunk.length} bytes at ${offset}` }],
    structuredContent: {
      bytes: Buffer.from(chunk).toString("base64"),
      offset, byteCount: chunk.length, totalBytes: data.length,
      hasMore: offset + chunk.length < data.length,
    },
  };
});
```

Client loops until `hasMore = false`:
```ts
while (hasMore) {
  const result = await app.callServerTool({ name: "read_data_bytes", arguments: { id, offset, byteCount: 512_000 } });
  const chunk = result.structuredContent;
  chunks.push(atob(chunk.bytes));
  offset += chunk.byteCount;
  hasMore = chunk.hasMore;
}
```

## Error reporting to model

```ts
await app.updateModelContext({
  content: [{ type: "text", text: "Error: transcription unavailable" }],
});
```

## Binary blobs via resources

```ts
// Server
server.registerResource("Video", new ResourceTemplate("video://{id}"), {
  mimeType: "video/mp4",
}, async (uri, { id }) => {
  const blob = Buffer.from(await getVideoData(id)).toString("base64");
  return { contents: [{ uri: uri.href, mimeType: "video/mp4", blob }] };
});

// Client
const result = await app.request({ method: "resources/read", params: { uri: `video://${id}` } }, ReadResourceResultSchema);
videoEl.src = `data:${result.contents[0].mimeType};base64,${result.contents[0].blob}`;
```

## Host context (theme, styling, fonts, safe areas)

```ts
app.onhostcontextchanged = (ctx) => {
  if (ctx.theme) applyDocumentTheme(ctx.theme);
  if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
  if (ctx.styles?.css?.fonts) applyHostFonts(ctx.styles.css.fonts);
  if (ctx.safeAreaInsets) { /* apply padding */ }
};
```

## Entering / exiting fullscreen

```ts
const newMode = ctx?.displayMode === "inline" ? "fullscreen" : "inline";
const result = await app.requestDisplayMode({ mode: newMode });
container.classList.toggle("fullscreen", result.mode === "fullscreen");
```

```css
#main { border-radius: var(--border-radius-lg); }
#main.fullscreen { border-radius: 0; }
```

## Model context updates

```ts
await app.updateModelContext({
  content: [{ type: "text", text: `User viewing page ${page}/${total}` }],
});
```

## Large follow-up messages

```ts
await app.updateModelContext({ content: [{ type: "text", text: fullTranscript }] });
await app.sendMessage({ role: "user", content: [{ type: "text", text: "Summarize the key points" }] });
```

## Persisting view state

Server returns `viewUUID` in `_meta`. Client uses `localStorage`:
```ts
app.ontoolresult = (result) => {
  viewUUID = result._meta?.viewUUID ? String(result._meta.viewUUID) : undefined;
  const saved = viewUUID ? localStorage.getItem(viewUUID) : null;
  if (saved) { /* restore */ }
};
// On state change: localStorage.setItem(viewUUID, JSON.stringify(state));
```

## Pausing offscreen views

```ts
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) startPolling();
    else stopPolling();
  });
});
observer.observe(container);
app.onteardown = async () => { observer.disconnect(); stopPolling(); return {}; };
```

## Lowering perceived latency

```ts
app.ontoolinputpartial = (params) => {
  preview.textContent = params.arguments?.code ?? "";
  preview.style.display = "block";
};
app.ontoolinput = (params) => {
  preview.style.display = "none";
  render(params.arguments?.code);
};
```

Partial arguments are "healed" JSON — don't rely on them for critical operations.

## View persistence (Brick Builder pattern)

Every model-visible tool with `resourceUri` creates a NEW iframe. Only ONE tool should have `AppConfig(resource_uri=...)`. All update tools are plain `@mcp.tool()` (no `AppConfig`). The View polls server state to pick up changes.

```python
RESOURCE_URI = "ui://viewer/app.html"

# ONLY entry-point tools create the iframe
@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI))
async def view_document(ref: str, pages: str) -> ToolResult: ...

# State-mutation tools — plain, no AppConfig, no new iframe
@mcp.tool()
async def viewer_set_highlight(term: str) -> ToolResult:
    state = await get_active_state()
    state.highlight_term = term
    await put_state(state)
    return ToolResult(content=[...])

@mcp.tool()
async def viewer_go_to_page(page: int) -> ToolResult: ...

# App-only polling tool
@mcp.tool(app=AppConfig(resource_uri=RESOURCE_URI, visibility=["app"]))
async def get_viewer_state(view_id: str) -> ToolResult:
    return ToolResult(structured_content=state.model_dump())
```

## Per-view state (multi-user)

Module-level state is shared across all users. Use per-view state keyed by `view_id` with TTL:

```python
# models.py — all Pydantic models in one place
class ViewerState(BaseModel):
    view_id: str = ""
    version: int = 0
    image_urls: list[str] = []
    highlight_term: str = ""

# state.py — store logic only
from key_value.aio.stores.memory import MemoryStore
from myapp.models import ViewerState

_store = MemoryStore(max_entries_per_collection=64)
latest_view_id: str = ""

async def get_state(view_id: str) -> ViewerState:
    data = await _store.get(key=view_id, collection="viewer")
    return ViewerState.model_validate(data) if data else ViewerState(view_id=view_id)

async def get_active_state() -> ViewerState:
    if not latest_view_id:
        raise LookupError("No viewer is open.")
    return await get_state(latest_view_id)

async def put_state(state: ViewerState) -> dict:
    global latest_view_id
    state.version += 1
    data = state.model_dump()
    await _store.put(key=state.view_id, value=data, collection="viewer", ttl=600)
    latest_view_id = state.view_id
    return data
```

## autoResize: false for flexible-height content

Default `autoResize` uses `ResizeObserver` which causes infinite resize loops with content that can grow (document viewers, lists). Disable it and send size manually in inline mode:

```typescript
new App({...}, { availableDisplayModes: ["inline", "fullscreen"] }, { autoResize: false });
```

```css
.main { width: 100%; height: 100vh; overflow: hidden; }
```

```svelte
$effect(() => {
  if (!app || isFullscreen) return;
  app.sendSizeChanged({ height: 550 });
});
```

When default `autoResize` works fine: Three.js canvas, fixed-size charts — content with stable dimensions.

## Fullscreen timing

Request fullscreen after `connect()`. Derive `isFullscreen` from `hostContext.displayMode`:

```svelte
let isFullscreen = $derived(hostContext?.displayMode === "fullscreen");

// After connect:
instance.requestDisplayMode({ mode: "fullscreen" }).catch(() => {});
```

## Stale state on data change

When the View receives new URLs (via poll), clear ALL internal caches: page cache, thumbnail cache, in-flight requests, search results, scroll position. But only if URLs actually changed — highlight-only updates should NOT reset caches.

## Command queue (alternative to flat state)

For apps with multiple distinct operations (navigate, search, annotate) that shouldn't overwrite each other, use typed commands instead of flat state replacement:

```typescript
type Command =
  | { type: "navigate"; page: number }
  | { type: "search"; query: string }
  | { type: "highlight"; id: string; query: string };

// Server: model tool enqueues, app-only tool dequeues
server.registerTool("interact", async ({ action, page }) => {
  commandQueue.push({ type: "navigate", page });
});
server.registerTool("poll_commands", async ({ viewUUID }) => {
  return { commands: commandQueue.drain(viewUUID) };
});
```

Flat state polling is simpler but loses concurrent commands. Use command queues when operations are independent and shouldn't overwrite each other.

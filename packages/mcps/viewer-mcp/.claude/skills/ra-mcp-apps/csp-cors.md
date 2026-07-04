# CSP & CORS for MCP Apps

MCP Apps run in sandboxed iframes with no same-origin server. Any network requests need CSP configuration.

**CSP** controls what the browser allows. Declare all origins in `_meta.ui.csp`.
**CORS** controls what the API server allows. Use `_meta.ui.domain` for stable origins.

## CSP Configuration

```python
@mcp.resource("ui://app/view.html", app=AppConfig(
    csp=ResourceCSP(
        resource_domains=["https://cdn.example.com"],     # <img>, <script>, <link>, <style>
        connect_domains=["https://api.example.com"],       # fetch(), XHR, WebSocket
        frame_domains=["https://youtube.com"],             # nested iframes
    )
))
```

## Default CSP (deny-by-default)

| Action | Allowed? | Enable with |
|--------|----------|-------------|
| Inline `<script>` and `<style>` | Yes | — |
| External `<script src="...">` | No | `resource_domains` |
| External `<img src="...">` | No | `resource_domains` |
| `fetch("https://...")` | No | `connect_domains` |
| WebSocket | No | `connect_domains` |
| Nested iframe | No | `frame_domains` |
| `data:` URIs | Yes | — |

## Stable Origins (CORS)

For APIs that allowlist specific origins:

```ts
function computeAppDomainForClaude(mcpServerUrl: string): string {
  const hash = crypto.createHash("sha256").update(mcpServerUrl).digest("hex").slice(0, 32);
  return `${hash}.claudemcpcontent.com`;
}

// Set in resource contents, not registerAppResource config
_meta: { ui: { domain: APP_DOMAIN, csp: { connectDomains: ["https://api.example.com"] } } }
```

## Common Mistakes

| Symptom | Fix |
|---------|-----|
| Image doesn't render | Add domain to `resource_domains` |
| `fetch()` fails | Add domain to `connect_domains` (not `resource_domains`) |
| Font doesn't load | Add font CDN to `resource_domains` |
| Google Fonts | Need BOTH `fonts.googleapis.com` AND `fonts.gstatic.com` in `resource_domains` |

# Testing MCP Apps

## Test with basic-host

```bash
git clone https://github.com/modelcontextprotocol/ext-apps.git
cd ext-apps && npm install && cd examples/basic-host
SERVERS='["http://localhost:3001/mcp"]' npm start
# Open http://localhost:8080
```

Debug panels: Tool Input, Tool Result, Messages, Model Context. Console logs prefixed `[HOST]`.

## Test with Claude.ai / VS Code

- Claude.ai: Add as remote MCP server or desktop extension
- VS Code Insiders: `.vscode/mcp.json` with `{ "servers": { "my-app": { "type": "http", "url": "http://localhost:3001/mcp" } } }`
- Goose: See https://block.github.io/goose/docs/getting-started/using-extensions/

## Expose local servers

**ngrok** (recommended — stable SSE):
```bash
ngrok http 3001
# Add https://<id>.ngrok-free.app/mcp to Claude
```

**cloudflared** (free, but drops SSE connections):
```bash
npx cloudflared tunnel --url http://localhost:3001
# URL changes on restart
```

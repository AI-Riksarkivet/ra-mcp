.PHONY: install build dev serve serve-stdio inspect inspect-verbose clean all

# Install all dependencies
install:
	npm install
	uv sync

# Build the frontend
build:
	npm run build

# Watch mode for frontend development
dev:
	npm run dev

# Run server in HTTP mode (for testing with basic-host)
serve: build
	@lsof -ti:3001 | xargs kill -9 2>/dev/null || true
	uv run python server.py

# Run server in stdio mode (for Claude Desktop)
serve-stdio: build
	uv run python server.py --stdio

# Open MCPJam inspector (run 'make serve' first in another terminal)
inspect:
	@echo "Opening inspector for http://localhost:3001/mcp"
	@echo "Note: Run 'make serve' in another terminal first"
	npx @mcpjam/inspector@latest --url http://localhost:3001/mcp

# Open MCPJam inspector with verbose logging
inspect-verbose:
	@echo "Opening inspector for http://localhost:3001/mcp (verbose)"
	@echo "Note: Run 'make serve' in another terminal first"
	npx @mcpjam/inspector@latest -v --url http://localhost:3001/mcp

# Clean build artifacts
clean:
	rm -rf dist node_modules .venv

# Full setup: install and build
all: install build

# Expose local server to the internet using Cloudflare Tunnel, than add: <tunnel_url>/mcp
tunnel: 
	npx cloudflared tunnel --url http://localhost:3001
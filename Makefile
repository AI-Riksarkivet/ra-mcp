.PHONY: install serve serve-http inspect format lint typecheck check test ci changelog release clean

# Install dependencies
install:
	uv sync

# Run MCP server (stdio transport)
serve:
	uv run ra serve

# Run MCP server (HTTP/SSE transport)
serve-http:
	uv run ra serve --port 8000

# Open MCP Inspector
inspect:
	npx @modelcontextprotocol/inspector uv run ra serve

# Format code
format:
	uv run ruff format .

# Lint and auto-fix
lint:
	uv run ruff check --fix .

# Type check
typecheck:
	uvx ty check

# Local code quality checks (format + lint + typecheck)
check: format lint typecheck

# Run tests
test:
	uv run pytest

# Run full CI pipeline via Dagger (same as GitHub Actions)
ci:
	dagger call checks
	dagger call test

# Generate changelog from conventional commits
changelog:
	uvx git-cliff --output CHANGELOG.md

# Cut a release: make release VERSION=0.5.0
release:
ifndef VERSION
	$(error VERSION is required. Usage: make release VERSION=0.5.0)
endif
	@echo "Releasing v$(VERSION)..."
	sed -i 's/^version = ".*"/version = "$(VERSION)"/' pyproject.toml
	git add pyproject.toml
	git commit -m "chore: bump version to $(VERSION)"
	git tag "v$(VERSION)"
	git push && git push --tags
	@echo "Done. release.yml will create the GitHub Release."

# Clean build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	rm -rf dist/ build/ *.egg-info

# Contributing to RA-MCP

## Development Setup

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for package management
- Git

### Installation
```bash
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
cd ra-mcp
uv sync
source .venv/bin/activate
```

## Contributing Process

### Issues
- Search existing issues before creating new ones
- Use issue templates when available
- Provide clear reproduction steps for bugs

### Code Standards
- Follow existing code style
- Use descriptive variable and function names
- Keep functions small and focused
- Add type hints for new code
- Write tests for new functionality

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ra_mcp
```

### Commits
Follow [Conventional Commits](https://conventionalcommits.org/):
```
feat: add keyword highlighting
fix: resolve timeout issues
docs: update API documentation
test: add integration tests
```

Sign commits with DCO:
```bash
git commit -s -m "your message"
```

### Pull Requests
- Keep changes focused and small
- Update documentation for API changes
- Ensure tests pass
- Link to related issues

## Code Review
- At least one maintainer review required
- Address feedback promptly
- CI pipeline must pass

## License
By contributing, you agree your contributions will be licensed under Apache License 2.0.
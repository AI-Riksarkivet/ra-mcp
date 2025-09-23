<!--
Sync Impact Report
Version change: 1.1.2 → 2.0.0
Modified principles:
- Principle IV: Changed from "Caching and Performance" to "API Performance and Reliability"
  - Old: MCP must implement response caching
  - New: MCP must rely on Riksarkivet's API caching (no local cache)
Added sections: None
Removed sections: None
Changes made:
- BREAKING: Removed local caching requirement from Principle IV
- Updated Code Organization to explicitly state no local caching
- Shifted focus to API reliability and error handling
Templates requiring updates:
✅ plan-template.md (references constitution v2.1.1, needs update to v2.0.0)
⚠ spec-template.md (no constitution references found)
⚠ tasks-template.md (may need to remove cache-related tasks)
⚠ command templates (directory not found)
⚠ CLAUDE.md (mentions cache.py which should be removed)
Follow-up TODOs:
- RATIFICATION_DATE set to TODO (pending user confirmation)
- Remove cache.py from src/ra_mcp/
- Update CLAUDE.md to remove cache references
- Create Dockerfile for containerization
- Create Dagger pipeline in Go under .dagger/ directory
- Configure Docker Hub repository and credentials
-->

# RA-MCP Constitution

## Core Principles

### I. MCP-First Architecture
Every feature must be exposed through the Model Context Protocol interface. Tools must follow MCP specification standards for consistent integration. The server must support multiple transport protocols (stdio, SSE/HTTP) for flexibility.

### II. API Client Modularity
Core API functionality must be separated from MCP server implementation. The `ra_core` module must be independently testable and reusable. Business logic must not depend on specific transport mechanisms.

### III. Test-Driven Development
Tests must be written before implementation for all new features. Every public API must have comprehensive test coverage. Integration tests must validate MCP tool contracts.

### IV. API Performance and Reliability
The MCP server must rely on Riksarkivet's API-level caching, not implement its own cache layer. Performance metrics must be monitored for API response times. Error handling must gracefully manage API rate limits and failures.

### V. Documentation Standards
Every MCP tool must have clear usage documentation with examples. API endpoints and data formats must be documented in CLAUDE.md. User-facing documentation must prioritize clarity over technical detail.

### VI. Reproducible CI/CD
All builds must be containerized using Docker for consistency. CI pipelines must be defined as code using Dagger. Environments must be reproducible across development, testing, and production. Production artifacts must be published to Docker Hub for distribution.

## Implementation Standards

### Technology Stack
- **Language**: Python 3.12+
- **MCP Framework**: FastMCP 2.7+
- **HTTP Client**: httpx for async operations
- **CLI Framework**: Typer for command-line interface
- **Dependency Management**: uv for package management
- **Containerization**: Docker for deployment and testing
- **CI/CD**: Dagger for pipeline-as-code

### Code Organization
- `src/ra_mcp/` contains all server implementation
- Core functionality separated into `ra_core.py`
- MCP tools defined in `tools.py`
- Formatters and utilities in dedicated modules
- CLI interface maintained separately from MCP server
- `.dagger/` contains Go-based CI pipeline definitions
- No local caching layer - rely on Riksarkivet API caching

### Testing Requirements
- Contract tests for all MCP tool definitions
- Unit tests for core API client functionality
- Integration tests for end-to-end workflows
- Mock external API calls in tests to ensure reliability

## Development Workflow

### CI/CD Standards
- **Dockerfile**: Multi-stage builds for optimal image size
- **Base Image**: Official Python slim images only
- **Dagger Pipeline**: Written in Go, located in `.dagger/` directory
- **Pipeline Structure**: Define build, test, and deploy stages as Go modules
- **Artifact Registry**: Publish container images to Docker Hub
- **Image Tagging**: Use semantic versioning and commit SHA for tags
- **Environment Parity**: Development containers must match production
- **Secrets Management**: Never embed secrets in images or pipeline code
- **Cache Optimization**: Leverage Docker layer caching and Dagger caching

### Branch Strategy
- Feature branches follow pattern: `feature-description`
- All changes must go through pull request review
- Main branch must remain stable and deployable

### Quality Gates
- All tests must pass before merging
- Code must follow Python formatting standards (ruff/black)
- Documentation must be updated with code changes
- CLAUDE.md must reflect any new commands or features
- Docker build must succeed without warnings
- Dagger CI pipeline must pass all stages

## Governance

### Amendment Process
- Constitutional changes require explicit documentation of rationale
- Version bumps follow semantic versioning:
  - MAJOR: Breaking changes to MCP interface or core principles
  - MINOR: New principles or significant expansions
  - PATCH: Clarifications and minor adjustments
- All amendments must be reflected in dependent templates

### Compliance Review
- Every pull request must verify constitutional compliance
- Complexity additions must be justified against simpler alternatives
- Use CLAUDE.md for runtime development guidance
- Templates in `.specify/templates/` must align with principles

### Decision Records
- Significant architectural decisions must be documented
- Trade-offs must be explicitly stated
- Alternative approaches must be recorded with rejection rationale

**Version**: 2.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Awaiting user confirmation | **Last Amended**: 2025-09-23
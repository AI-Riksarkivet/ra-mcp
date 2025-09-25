<!--
Sync Impact Report
Version change: 2.0.0 → 2.1.0
Modified principles: None
Added sections:
- Principle VII: Open Source Excellence
- Open Source Standards section with Security Requirements, Contribution Guidelines, and Repository Health
Removed sections: None
Changes made:
- Added Principle VII for open source governance
- Specified Apache License 2.0 requirement
- Added security standards for public repositories
- Defined contribution guidelines and English language requirement
- Added repository health requirements
Templates requiring updates:
✅ plan-template.md (references constitution v2.1.1, needs update to v2.1.0)
⚠ spec-template.md (no constitution references found)
⚠ tasks-template.md (may need open source setup tasks)
⚠ CLAUDE.md (mentions cache.py which should be removed)
Follow-up TODOs:
- RATIFICATION_DATE set to TODO (pending user confirmation)
- Create LICENSE file with Apache License 2.0
- Create SECURITY.md for vulnerability reporting
- Create CONTRIBUTING.md with contribution guidelines
- Create CODE_OF_CONDUCT.md
- Create .env.example file
- Remove cache.py from src/ra_mcp/
- Update CLAUDE.md to remove cache references
- Create Dockerfile for containerization
- Create Dagger pipeline in Go under .dagger/ directory
- Configure Docker Hub repository and credentials
-->

# RA-MCP Constitution

## Core Principles

### I. MCP-First Architecture
Every feature must be exposed through the Model Context Protocol interface. Tools must follow MCP specification standards for consistent integration. The server must support multiple transport protocols (stdio, HTTP) for flexibility.

### II. API Client Modularity
Core API functionality must be separated from MCP server implementation. Business logic must not depend on specific transport mechanisms.

### III. Documentation Standards
Every MCP tool must have clear usage documentation with examples. Please always use the descriptions of how to write good tools from fastmcp docs: https://gofastmcp.com/servers/tools.md.  API endpoints and data formats must be documented in CLAUDE.md. User-facing documentation must prioritize clarity over technical detail.

### IV. Reproducible CI/CD
All builds must be containerized using Docker for consistency. CI pipelines must be defined as code using Dagger. Environments must be reproducible across development, testing, and production. Production artifacts must be published to Docker Hub for distribution. 

### V. Open Source Excellence
All code must be developed with public visibility in mind. The project must be licensed under Apache License 2.0 for patent protection and commercial compatibility. Security-sensitive information must never be committed to the repository. All documentation and code comments must be in English for international accessibility.

## Implementation Standards


### Technology Stack
- **Language**: Python 3.12+
- **MCP Framework**: FastMCP 2.7+
- **HTTP Client**: httpx for async operations
- **CLI Framework**: Typer for command-line interface
- **Dependency Management**: uv for package management, but also uses this linting and formatting.
- **Containerization**: Docker for deployment and testing
- **CI/CD**: Dagger for pipeline-as-code
- **License**: Apache License 2.0

### Code Organization
- `src/ra_mcp/` contains all server implementation
- Core functionality separated into `ra_core.py`
- MCP tools defined in `tools.py`
- Formatters and utilities in dedicated modules
- CLI interface maintained separately from MCP server
- `.dagger/` contains Go-based CI pipeline definitions
- No local caching layer - rely on Riksarkivet API caching

### Code Quality Principles

#### Naming and Readability
- **Use Meaningful Names**: Choose descriptive and unambiguous names for variables, functions, and classes that clearly state their purpose
- **Prioritize Clarity Over Cleverness**: Write code that is straightforward and easy to understand, rather than being overly complex or obscure
- **Code Like a Story**: The code should explain itself, making it understandable without needing many comments
- **Follow Consistent Formatting**: Maintain a consistent style throughout the codebase to avoid confusion and make the code more predictable

#### Functions and Methods
- **Keep Functions Small and Focused**: Functions should do one thing and do it well, following the Single Responsibility Principle (SRP)
- **Limit Arguments**: Functions with fewer arguments are generally easier to understand and manage
- **Avoid Side Effects**: Functions should not have unintended consequences that affect other parts of the system
- **Use Early Returns**: Return values as soon as possible to reduce nesting of conditional statements

#### Code Structure and Organization
- **DRY (Don't Repeat Yourself)**: Avoid duplicating code; instead, create reusable components
- **Separate Concerns**: Organize code into logical modules or units, with each handling a specific task
- **Keep Code Vertically Dense**: Place related pieces of code and dependent functions close to each other
- **Use White Space**: Use white space to group related code and separate dissimilar pieces, improving visual clarity

#### Other Key Principles
- **YAGNI (You Ain't Gonna Need It)**: Don't implement functionality that isn't currently required; focus only on what's necessary now
- **Test Your Code**: Write automated tests to ensure that the code behaves as expected, making changes safer and more predictable
- **Replace Magic Numbers**: Use named constants instead of hardcoded values to improve readability and maintainability
- **The Boy Scout Rule**: Always strive to leave the code better than you found it

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

## Open Source Standards

### Security Requirements
- **No Secrets in Code**: API keys, credentials, and tokens must use environment variables
- **Dependency Scanning**: Automated security scanning for all dependencies
- **Security Disclosure**: SECURITY.md file with vulnerability reporting process
- **Public Safety**: Example configurations must use dummy values
- **.env.example**: Provide template without actual credentials

### Contribution Guidelines
- **Pull Request Process**: All changes via PR with at least one review
- **Commit Standards**: Follow Conventional Commits specification
- **Testing Required**: New features must include tests
- **Documentation**: Update docs with code changes
- **English Only**: All code, comments, and documentation in English
- **Sign-off**: Contributors must sign commits with DCO (git commit -s)

### Repository Health
- **License File**: Apache License 2.0 in repository root
- **Contributing Guide**: CONTRIBUTING.md with clear instructions
- **Code of Conduct**: Respectful community standards
- **Issue Templates**: Structured bug reports and feature requests
- **Changelog**: Track all changes following Keep a Changelog format

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

**Version**: 2.1.0 | **Ratified**: TODO(RATIFICATION_DATE): Awaiting user confirmation | **Last Amended**: 2025-09-23
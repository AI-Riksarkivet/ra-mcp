# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-02-09

### Added
- Add Helm chart for Kubernetes deployment
- Add /health endpoint and update probes
- Add tool timeouts to prevent indefinite hangs
- Add tags to tools for filtering and categorization
- Add read-only and open-world annotations to tools
- Add version baselines to all tools
- Add /ready endpoint and separate liveness from readiness

### CI/CD
- Upgrade actions/checkout to v5 across all workflows

### Changed
- Replace sys.argv manipulation with direct function parameters
- Replace import_server with namespaced mount

### Fixed
- Add tmp volume and chart icon
- Use importlib.metadata for version single source of truth
- Remove pip via rm instead of invoking pip uninstall

### Miscellaneous
- Rewrite Makefile to match current project structure
- Remove unused parseBuildArgs function
- Add PEP 561 py.typed markers to all packages
- Add git-cliff changelog generation
- Bump version to 0.4.0

## [0.3.0] - 2026-02-09

### Added
- Add sort, date range, name, and place search parameters
- Add OpenTelemetry instrumentation and upgrade to FastMCP 3.0
- Add trace tree display to verify-telemetry output

### CI/CD
- Add CodeQL workflow for SAST analysis
- Add workflow_dispatch trigger
- Pin all GitHub Actions and container images by SHA hash

### Changed
- Import URL constants from config instead of duplicating them
- Simplify browse command logic
- Simplify search command logic

### Documentation
- Update package READMEs to match current architecture
- Add observability and telemetry section to CLAUDE.md
- Add CodeQL badge to README

### Fixed
- Add error logging, span recording, and input validation

### Miscellaneous
- Remove accidentally committed build artifacts
- Bump version to 0.3.0

### Performance
- Eliminate duplicate OAI-PMH request in browse_document

## [0.2.13] - 2026-02-06

### Changed
- Move error formatting to formatter class

### Documentation
- Add Python tooling and quality badges
- Remove duplicate person name search example

### Fixed
- Add explicit top-level permissions for least privilege
- Rebuild test infrastructure to support missing test suite

### Miscellaneous
- Add Dependabot configuration for automated updates
- Update docs to match 8-package architecture, align versions, remove dead dagger code
- Bump version to 0.2.13

## [0.2.12] - 2026-02-06

### Added
- Extract real BuildKit attestations for Scorecard

### Miscellaneous
- Bump version to 0.2.12

## [0.2.11] - 2026-02-06

### Added
- Add OpenSSF Scorecard and accurate SLSA level
- Export attestations as release assets for Scorecard

### Documentation
- Add SLSA, Sigstore, and SBOM badges to README

### Miscellaneous
- Bump version to 0.2.11

## [0.2.10] - 2026-02-06

### Added
- Add Cosign image signing with keyless signing

### Fixed
- Correct SBOM export to write file to workspace

### Miscellaneous
- Bump version to 0.2.10

## [0.2.9] - 2026-02-06

### Added
- Add attestation verification and inspection tools
- Add SLSA Level 3 attestations with signing
- Unify publish workflows to single Alpine-only workflow

### Documentation
- Remove ATTESTATIONS.md documentation
- Simplify SECURITY.md and sync lockfile

### Fixed
- Resolve SLSA L3 workflow secrets syntax error
- Set private-repository false for SLSA L3 workflow
- Workaround SLSA generator private repo detection bug
- Simplify SLSA L3 build to amd64 only
- Disable checks and PyPI publishing in workflow

### Miscellaneous
- Bump version to 0.2.9 for SLSA L3 release
- Remove experimental SLSA L3 workflow
- Revert version to 0.2.8
- Bump version to 0.2.9

## [0.2.8] - 2026-02-06

### Added
- Add comprehensive CLI interface and refactor ra_core into modular architecture (**BREAKING**)
- Establish project constitution v2.0.0 (**BREAKING**)
- Add project infrastructure and governance framework
- Add implementation quickstart and update task tracking
- Consolidate commands and enhance search functionality (**BREAKING**)
- Move document metadata inside display panels
- Add --show-links option to browse command
- Improve search context display and update terminology
- Rename --context to --browse in search command (**BREAKING**)
- Enhance search browse to prioritize multiple volumes
- Add document metadata support for browse operations
- Add --show-links option to search command
- Add enhanced progress feedback to search command
- Improve browse display with two-column layout and folder tree hierarchy
- Change default max-hits-per-vol from None to 3
- Preserve API highlighting and add debug output
- Add advanced Solr search syntax documentation
- Add logging for debugging API timeouts
- Add Trivy scanning and reduce CVEs by 67%
- Extract guide resources into separate ra-mcp-guide package (**BREAKING**)
- Show total hit count when results are truncated
- Add support for non-transcribed text search
- Add clickable links to view records on Riksarkivet website
- Display IIIF image manifest links in search results
- Add rich metadata and improve blank page handling
- Split search tool and enhance metadata display
- Convert IIIF manifest URLs to bildvisaren URLs
- Add multi-base-image support for flexible container builds
- Add comprehensive SBOM and attestation support

### Build
- Add project scaffolding and development tools
- Improve dagger pipeline and dockerfile optimization

### Changed
- Eliminate code duplication between CLI and MCP interfaces
- Move PID resolution to PageContextService
- Split DisplayService into interface-specific services
- Consolidate hardcoded URLs into config module
- Remove duplicate arkis prefix removal function
- Simplify SearchOperations by removing intermediate methods
- Extract manifest URL directly from API response
- Unify search context and browse display logic
- Remove debug code and organize imports
- Consolidate display services into unified service with formatter injection (**BREAKING**)
- Rename UnifiedDisplayService to DisplayService with show_border parameter
- Remove --context-padding option
- Consolidate methods and enhance documentation
- Remove context display parameters from search tool
- Remove context_padding functionality
- Move group_hits_by_document closer to usage
- Remove unused utility functions
- Remove --browse flag from search command
- Move browse display logic to formatter layer
- Move browse error formatting to display service
- Move search results display to service layer
- Extract progress helpers to cli_progress module
- Move status messages to display service
- Inline server startup functions into serve command
- Move get_http_client to http_client module
- Split SearchOperations into SearchOperations and BrowseOperations
- Remove context enrichment functionality
- Merge PageContextService into BrowseOperations
- Move pagination logic to search_tools
- Move summary extraction to SearchResult model
- Split DisplayService into separate browse and search services
- Switch to Alpine base and remove lxml dependency
- Migrate to modular workspace architecture (**BREAKING**)
- Inline progress indicators into command files
- Split monolithic mcp.py into modular structure
- Replace flat SearchHit with hierarchical SearchRecord (**BREAKING**)
- Introduce RecordsResponse matching complete API structure
- Align SearchResult and RecordsResponse with Search API specification
- Align browse models with OAI-PMH API response structure
- Simplify SearchAPI client and align parameter naming with API
- Move formatters from core to search package
- Reorganize services directory into operations and formatters
- Remove display service and base formatter abstractions
- Split search package into search-cli and search-mcp (**BREAKING**)
- Adopt explicit root layout with server at root
- Move formatters to presentation layer packages
- Split search and browse into separate domain packages (**BREAKING**)
- Move models from core to domain packages
- Rename core to common and move domain utilities (**BREAKING**)
- Rename core to common and move domain-specific utilities
- Simplify root help text to be general instead of search-specific
- Rename guide package to guide-mcp for consistency
- Simplify MCP package module names
- Simplify CLI package module names
- Rename CLI flags to match API and improve clarity
- Add typed models and fix all type checking errors

### Documentation
- Consolidate tool documentation into root README
- Rewrite README with user-focused structure and professional tone
- Consolidate API documentation and data sources sections
- Remove redundant Riksarkivet documentation reference
- Remove performance and architecture sections from technical details
- Add open source standards with apache license
- Add comprehensive clean code principles
- Add feature specification for riksarkivet document search system
- Add dagger build and publish documentation
- Update README to reflect consolidated CLI structure
- Fix workflow numbering and improve examples
- Add logo to README header
- Improve Output Features section with examples and better formatting
- Add links to HTRflow PyPI and Docker Hub repository
- Update README examples with authentic historical data
- Rewrite MCP server implementation section with accurate tool documentation
- Reorganize assets and improve README formatting
- Reorganize project specification and update implementation status
- Add comprehensive architecture diagrams with Mermaid visualizations
- Fix architecture diagram accuracy and improve grouping
- Improve parse_page_range function docstring
- Improve docstrings for SearchOperations class methods
- Update search documentation with wildcard and fuzzy search
- Add proximity search example
- Add term boosting and proximity search examples
- Add Boolean operators documentation
- Add comprehensive search syntax documentation
- Reorder search options in README
- Enhance tool descriptions for search and browse
- Update Docker publish example with direct username
- Enhance tool description with context and translation guidance
- Improve search syntax examples and error messages
- Clarify boolean search grouping requirements
- Fix build and publish instructions
- Improve CLAUDE.md with comprehensive documentation
- Improve help text for search and browse commands
- Update search tool documentation with new search modes

### Fixed
- Correct import and method references for CLI functionality
- Improve search context display and page number formatting
- Fix manifest ID handling and remove broken PID conversion
- Correct SearchSummary attribute access in CLI commands
- Fix SearchSummary attribute error in display functions
- Improve search progress messaging
- Make search highlighting case-insensitive in browse mode
- Improve browse command display and fix type annotation
- Use accurate 'volumes' terminology in search progress messages
- Correct transport type and search summary access
- Remove duplicate parameters and fix module import
- Correct logo path in README
- Remove snippet truncation in search results
- Add missing format_search_summary method
- Extract page number from last segment of page ID
- Upgrade pip to 25.3 to fix CVE-2025-8869
- Correct typo manifset_id to manifest_id
- Correct root package build configuration
- Resolve dagger-for-github multiline args syntax error
- Disable PyPI publishing, focus on Docker releases only

### Miscellaneous
- Remove obsolete ra_tools.py wrapper
- Upgrade fastmcp and dependencies
- Add conventional commit slash command
- Bump version to 0.2.0 and improve publish workflow (**BREAKING**)
- Remove unused demo directory
- Bump version to 0.2.1



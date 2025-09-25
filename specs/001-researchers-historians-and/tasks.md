# Tasks: Riksarkivet Historical Document Search and Access System

**Input**: Design documents from `/specs/001-researchers-historians-and/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   ✅ Implementation plan loaded successfully
   ✅ Extracted: Python 3.12+, FastMCP, httpx, typer, Docker, Dagger
2. Load optional design documents:
   ✅ spec.md: Extracted entities and functional requirements
   ❌ data-model.md: Missing - will create in Phase 3.1
   ❌ contracts/: Missing - will create in Phase 3.1
   ❌ research.md: Missing - tech decisions in plan.md
3. Generate tasks by category:
   ✅ Setup: Docker, Dagger, governance files, missing design docs
   ✅ Tests: MCP tool contract tests, integration scenarios
   ✅ Core: MCP tools, pydantic models, CLI enhancements
   ✅ Integration: performance optimization, error handling
   ✅ Polish: unit tests, documentation, validation
4. Apply task rules:
   ✅ Different files = mark [P] for parallel
   ✅ Same file (server.py, search_tools.py) = sequential (no [P])
   ✅ Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   ✅ All MCP tools have contract tests
   ✅ All entities have model tasks
   ✅ All functional requirements covered
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/ra_mcp/`, `tests/` at repository root
- Paths shown below are absolute from repository root

## Phase 3.1: Setup
- [ ] T001 [P] Create Dockerfile with multi-stage Python 3.12+ build at `/home/coder/ra-mcp/Dockerfile`
- [ ] T002 [P] Create .dagger/main.go and CI pipeline structure at `/home/coder/ra-mcp/.dagger/main.go`
- [ ] T003 [P] Create SECURITY.md vulnerability reporting guide at `/home/coder/ra-mcp/SECURITY.md`
- [ ] T004 [P] Create CONTRIBUTING.md with contribution guidelines at `/home/coder/ra-mcp/CONTRIBUTING.md`
- [ ] T005 [P] Create CODE_OF_CONDUCT.md community standards at `/home/coder/ra-mcp/CODE_OF_CONDUCT.md`
- [ ] T006 [P] Create .env.example environment template at `/home/coder/ra-mcp/.env.example`
- [ ] T007 [P] Create data-model.md with pydantic models for entities at `/home/coder/ra-mcp/specs/001-researchers-historians-and/data-model.md`
- [ ] T008 [P] Create contracts/search_transcribed.yaml OpenAPI schema at `/home/coder/ra-mcp/specs/001-researchers-historians-and/contracts/search_transcribed.yaml`
- [ ] T009 [P] Create contracts/browse_document.yaml OpenAPI schema at `/home/coder/ra-mcp/specs/001-researchers-historians-and/contracts/browse_document.yaml`
- [ ] T010 [P] Create contracts/get_document_structure.yaml OpenAPI schema at `/home/coder/ra-mcp/specs/001-researchers-historians-and/contracts/get_document_structure.yaml`

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T011 [P] Contract test for search_transcribed MCP tool at `/home/coder/ra-mcp/tests/contract/test_search_transcribed.py`
- [ ] T012 [P] Contract test for browse_document MCP tool at `/home/coder/ra-mcp/tests/contract/test_browse_document.py`
- [ ] T013 [P] Contract test for get_document_structure MCP tool at `/home/coder/ra-mcp/tests/contract/test_get_document_structure.py`
- [ ] T014 [P] Integration test researcher keyword discovery workflow at `/home/coder/ra-mcp/tests/integration/test_researcher_workflow.py`
- [ ] T015 [P] Integration test document structure analysis workflow at `/home/coder/ra-mcp/tests/integration/test_document_analysis.py`
- [ ] T016 [P] Integration test AI assistant research patterns at `/home/coder/ra-mcp/tests/integration/test_ai_assistant.py`
- [ ] T017 [P] Integration test performance optimization scenarios at `/home/coder/ra-mcp/tests/integration/test_performance_scenarios.py`

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T018 [P] Historical Document model in `/home/coder/ra-mcp/src/ra_mcp/models/historical_document.py`
- [ ] T019 [P] Search Hit model in `/home/coder/ra-mcp/src/ra_mcp/models/search_hit.py`
- [ ] T020 [P] Document Page model in `/home/coder/ra-mcp/src/ra_mcp/models/document_page.py`
- [ ] T021 [P] IIIF Manifest model in `/home/coder/ra-mcp/src/ra_mcp/models/iiif_manifest.py`
- [ ] T022 [P] MCP Tool Response model in `/home/coder/ra-mcp/src/ra_mcp/models/mcp_response.py`
- [ ] T023 Enhance search_transcribed tool with improved parameter validation in `/home/coder/ra-mcp/src/ra_mcp/server.py`
- [ ] T024 Enhance browse_document tool with better error handling in `/home/coder/ra-mcp/src/ra_mcp/server.py`
- [ ] T025 Enhance get_document_structure tool with manifest optimization in `/home/coder/ra-mcp/src/ra_mcp/server.py`
- [ ] T026 [P] Enhanced SearchOperations service in `/home/coder/ra-mcp/src/ra_mcp/services/enhanced_search_operations.py`
- [ ] T027 [P] Performance monitoring service in `/home/coder/ra-mcp/src/ra_mcp/services/performance_monitor.py`

## Phase 3.4: Integration
- [ ] T028 Integrate enhanced models with MCP tools in `/home/coder/ra-mcp/src/ra_mcp/server.py`
- [ ] T029 [P] Enhanced typer CLI commands in `/home/coder/ra-mcp/src/ra_mcp/cli/enhanced_commands.py`
- [ ] T030 Configure response size optimization for token limits in `/home/coder/ra-mcp/src/ra_mcp/services/display_service.py`
- [ ] T031 Add concurrent request handling improvements in `/home/coder/ra-mcp/src/ra_mcp/services/search_operations.py`
- [ ] T032 Implement comprehensive error formatting in `/home/coder/ra-mcp/src/ra_mcp/formatters/mcp_formatter.py`

## Phase 3.5: Polish
- [ ] T033 [P] Unit tests for enhanced models at `/home/coder/ra-mcp/tests/unit/test_enhanced_models.py`
- [ ] T034 [P] Unit tests for performance monitoring at `/home/coder/ra-mcp/tests/unit/test_performance_monitor.py`
- [ ] T035 [P] Update CLAUDE.md with enhanced MCP tool documentation at `/home/coder/ra-mcp/CLAUDE.md`
- [ ] T036 [P] Create comprehensive API documentation at `/home/coder/ra-mcp/docs/api.md`
- [ ] T037 Performance benchmarking tests (<2 second response) at `/home/coder/ra-mcp/tests/performance/test_response_times.py`
- [ ] T038 Execute quickstart.md scenarios to validate implementation at `/home/coder/ra-mcp/specs/001-researchers-historians-and/quickstart.md`

## Dependencies
- Setup tasks (T001-T010) can run in parallel
- Tests (T011-T017) before implementation (T018-T032)
- Models (T018-T022) before service enhancements (T026-T027)
- T023-T025 sequential (same file: server.py)
- T028 requires T018-T027 completion
- Implementation before polish (T033-T038)

## Parallel Example
```
# Launch T001-T010 together:
Task: "Create Dockerfile with multi-stage Python 3.12+ build at /home/coder/ra-mcp/Dockerfile"
Task: "Create .dagger/main.go and CI pipeline structure at /home/coder/ra-mcp/.dagger/main.go"
Task: "Create SECURITY.md vulnerability reporting guide at /home/coder/ra-mcp/SECURITY.md"
Task: "Create data-model.md with pydantic models for entities at /home/coder/ra-mcp/specs/001-researchers-historians-and/data-model.md"

# Launch T011-T017 together:
Task: "Contract test for search_transcribed MCP tool at /home/coder/ra-mcp/tests/contract/test_search_transcribed.py"
Task: "Contract test for browse_document MCP tool at /home/coder/ra-mcp/tests/contract/test_browse_document.py"
Task: "Integration test researcher keyword discovery workflow at /home/coder/ra-mcp/tests/integration/test_researcher_workflow.py"
Task: "Integration test AI assistant research patterns at /home/coder/ra-mcp/tests/integration/test_ai_assistant.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each MCP tool → contract test task [P] (T011-T013)
   - Each tool → implementation task (T023-T025)

2. **From Data Model**:
   - Each entity → model creation task [P] (T018-T022)
   - Relationships → service layer tasks (T026-T027)

3. **From User Stories**:
   - Each quickstart scenario → integration test [P] (T014-T017)
   - Validation scenarios → execution task (T038)

4. **Ordering**:
   - Setup → Tests → Models → Services → Tools → Integration → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All MCP tools have corresponding contract tests (T011-T013)
- [x] All entities have model tasks (T018-T022)
- [x] All tests come before implementation (T011-T017 → T018-T032)
- [x] Parallel tasks truly independent ([P] tasks use different files)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
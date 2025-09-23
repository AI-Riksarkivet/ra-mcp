# Tasks: Riksarkivet Historical Document Search and Access System

**Input**: Design documents from `/specs/001-researchers-historians-and/`
**Prerequisites**: plan.md (✅), spec.md (✅)

## Execution Flow (main)
```
✅ 1. Load plan.md from feature directory
   → Implementation plan loaded successfully
   → Extracted: Python 3.12+, FastMCP, httpx, typer, Docker, Dagger
✅ 2. Load optional design documents:
   → spec.md: Extracted functional requirements and entities
   → No data-model.md or contracts/ - will create in Phase 1
✅ 3. Generate tasks by category:
   → Setup: governance files, Docker, dependencies
   → Tests: MCP tool contract tests, integration scenarios
   → Core: enhanced MCP tools, pydantic models, CLI improvements
   → Integration: performance optimization, error handling
   → Polish: documentation, quickstart guide
✅ 4. Apply task rules:
   → Infrastructure tasks marked [P] (independent files)
   → MCP tool enhancements sequential (shared mcp_tools.py)
   → Tests before implementation (TDD approach)
✅ 5. Number tasks sequentially (T001-T020)
✅ 6. Generate dependency graph with parallel execution
✅ 7. Create parallel execution examples for [P] tasks
✅ 8. Validate task completeness against functional requirements
✅ 9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/ra_mcp/`, `tests/` at repository root (matches current structure)
- All file paths shown are absolute from repository root

## Phase 3.1: Infrastructure Setup
- [ ] T001 [P] Create Dockerfile with multi-stage Python 3.12+ build at `/home/coder/ra-mcp/Dockerfile`
- [ ] T002 [P] Create SECURITY.md vulnerability reporting guide at `/home/coder/ra-mcp/SECURITY.md`
- [ ] T003 [P] Create CONTRIBUTING.md with contribution guidelines at `/home/coder/ra-mcp/CONTRIBUTING.md`
- [ ] T004 [P] Create CODE_OF_CONDUCT.md community standards at `/home/coder/ra-mcp/CODE_OF_CONDUCT.md`
- [ ] T005 [P] Create .env.example environment template at `/home/coder/ra-mcp/.env.example`
- [ ] T006 Create .dagger/main.go and CI pipeline structure at `/home/coder/ra-mcp/.dagger/`

## Phase 3.2: Design Documents (Phase 1 execution)
- [ ] T007 [P] Create data-model.md with enhanced pydantic models at `/home/coder/ra-mcp/specs/001-researchers-historians-and/data-model.md`
- [ ] T008 [P] Create contracts/search_transcribed.yaml OpenAPI schema at `/home/coder/ra-mcp/specs/001-researchers-historians-and/contracts/search_transcribed.yaml`
- [ ] T009 [P] Create contracts/browse_document.yaml OpenAPI schema at `/home/coder/ra-mcp/specs/001-researchers-historians-and/contracts/browse_document.yaml`
- [ ] T010 [P] Create contracts/get_document_structure.yaml OpenAPI schema at `/home/coder/ra-mcp/specs/001-researchers-historians-and/contracts/get_document_structure.yaml`
- [ ] T011 Create quickstart.md with researcher workflow scenarios at `/home/coder/ra-mcp/specs/001-researchers-historians-and/quickstart.md`

## Phase 3.3: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.4
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T012 [P] Contract test for search_transcribed MCP tool at `/home/coder/ra-mcp/tests/contract/test_search_transcribed.py`
- [ ] T013 [P] Contract test for browse_document MCP tool at `/home/coder/ra-mcp/tests/contract/test_browse_document.py`
- [ ] T014 [P] Contract test for get_document_structure MCP tool at `/home/coder/ra-mcp/tests/contract/test_get_document_structure.py`
- [ ] T015 [P] Integration test researcher keyword search workflow at `/home/coder/ra-mcp/tests/integration/test_researcher_workflow.py`
- [ ] T016 [P] Integration test AI assistant integration patterns at `/home/coder/ra-mcp/tests/integration/test_ai_assistant.py`

## Phase 3.4: Core Implementation (ONLY after tests are failing)
- [ ] T017 Enhance search_transcribed tool with better highlighting in `/home/coder/ra-mcp/src/ra_mcp/mcp_tools.py`
- [ ] T018 Enhance browse_document tool with improved navigation in `/home/coder/ra-mcp/src/ra_mcp/mcp_tools.py`
- [ ] T019 Enhance get_document_structure tool with better metadata in `/home/coder/ra-mcp/src/ra_mcp/mcp_tools.py`
- [ ] T020 [P] Create enhanced pydantic models for better AI integration at `/home/coder/ra-mcp/src/ra_mcp/models.py`
- [ ] T021 [P] Improve PlainTextFormatter for LLM token efficiency at `/home/coder/ra-mcp/src/ra_mcp/formatters.py`

## Phase 3.5: CLI and Performance
- [ ] T022 [P] Enhance typer-based CLI commands at `/home/coder/ra-mcp/src/ra_mcp/cli/main.py`
- [ ] T023 Implement response size optimization for token limits in `/home/coder/ra-mcp/src/ra_mcp/services/display_service.py`
- [ ] T024 Add concurrent request handling improvements in `/home/coder/ra-mcp/src/ra_mcp/services/search_operations.py`

## Phase 3.6: Documentation and Polish
- [ ] T025 [P] Update CLAUDE.md with enhanced MCP tool documentation at `/home/coder/ra-mcp/CLAUDE.md`
- [ ] T026 [P] Create unit tests for enhanced models at `/home/coder/ra-mcp/tests/unit/test_models.py`
- [ ] T027 [P] Create unit tests for formatters at `/home/coder/ra-mcp/tests/unit/test_formatters.py`
- [ ] T028 Execute quickstart.md scenarios to validate implementation at `/home/coder/ra-mcp/specs/001-researchers-historians-and/quickstart.md`

## Dependencies
**Critical Path**:
- Infrastructure setup (T001-T006) can run in parallel
- Design documents (T007-T011) can run in parallel after infrastructure
- Tests (T012-T016) MUST complete before implementation (T017-T024)
- T017-T019 are sequential (same file: mcp_tools.py)
- Documentation (T025-T028) can run in parallel after core implementation

**Blocking Relationships**:
- T017-T019 modify same file - must be sequential
- T012-T016 must fail before T017-T024 implementation
- T028 requires T017-T024 completion

## Parallel Example
```
# Phase 3.1 - Launch infrastructure tasks together:
Task: "Create Dockerfile with multi-stage Python 3.12+ build at /home/coder/ra-mcp/Dockerfile"
Task: "Create SECURITY.md vulnerability reporting guide at /home/coder/ra-mcp/SECURITY.md"
Task: "Create CONTRIBUTING.md with contribution guidelines at /home/coder/ra-mcp/CONTRIBUTING.md"
Task: "Create CODE_OF_CONDUCT.md community standards at /home/coder/ra-mcp/CODE_OF_CONDUCT.md"

# Phase 3.2 - Launch design documents together:
Task: "Create data-model.md with enhanced pydantic models"
Task: "Create contracts/search_transcribed.yaml OpenAPI schema"
Task: "Create contracts/browse_document.yaml OpenAPI schema"
Task: "Create contracts/get_document_structure.yaml OpenAPI schema"

# Phase 3.3 - Launch contract tests together:
Task: "Contract test for search_transcribed MCP tool at /home/coder/ra-mcp/tests/contract/test_search_transcribed.py"
Task: "Contract test for browse_document MCP tool at /home/coder/ra-mcp/tests/contract/test_browse_document.py"
Task: "Contract test for get_document_structure MCP tool at /home/coder/ra-mcp/tests/contract/test_get_document_structure.py"
```

## Functional Requirements Coverage
**Mapped to Tasks**:
- FR-001 (keyword search): T017, T012, T015
- FR-002 (highlighting): T017, T021
- FR-003 (browse by reference): T018, T013
- FR-004 (complete transcriptions): T018, T019
- FR-005 (high-res images): T019, T014
- FR-006 (AI integration): T016, T020, T021
- FR-007 (CLI interface): T022
- FR-008 (API interface): T017-T019 (MCP tools)
- FR-009 (metadata): T020, T021
- FR-010 (multi-page navigation): T018
- FR-011 (efficient handling): T023, T024

## Notes
- **[P] tasks**: Different files, can run in parallel
- **Sequential tasks**: T017-T019 modify mcp_tools.py sequentially
- **TDD Critical**: Tests T012-T016 MUST fail before implementing T017-T024
- **Performance targets**: <2 second response (T023), 100+ concurrent calls (T024)
- **Constitutional compliance**: All tasks align with MCP-First Architecture

## Task Generation Rules Applied
1. **From Plan.md**: Infrastructure tasks (T001-T006), tech stack implementation
2. **From Spec.md**: Functional requirements → implementation tasks
3. **From Entities**: Historical Document, Transcription, etc. → enhanced models (T020)
4. **From User Stories**: Researcher workflows → integration tests (T015-T016)
5. **Ordering**: Setup → Design → Tests → Implementation → Polish
6. **Parallel Marking**: Independent files marked [P], shared files sequential

## Validation Checklist
✅ **GATE: Checked before execution**
- [x] All functional requirements have corresponding tasks
- [x] All MCP tools have contract tests (T012-T014)
- [x] All tests come before implementation (T012-T016 → T017-T024)
- [x] Parallel tasks are truly independent ([P] tasks use different files)
- [x] Each task specifies exact absolute file path
- [x] No [P] task modifies same file as another [P] task
- [x] Constitutional principles addressed in infrastructure tasks
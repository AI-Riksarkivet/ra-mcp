# Quickstart Guide: Researcher Workflow Scenarios

## Overview

This quickstart guide demonstrates typical workflows for researchers, historians, and AI assistants using the enhanced RA-MCP server to access Swedish National Archives materials.

## Prerequisites

- RA-MCP server running (stdio or HTTP/SSE mode)
- Python 3.12+ with dependencies installed
- Access to Riksarkivet API endpoints

## Quick Start Commands

### Start the Server
```bash
# HTTP/SSE mode (recommended for AI assistants)
cd src/ra_mcp && python server.py --http

# Stdio mode (for Claude Desktop integration)
cd src/ra_mcp && python server.py
```

### Connect with Claude Code
```bash
# Add server to Claude Code
claude mcp add --transport sse ra-mcp http://localhost:8000/sse

# Verify connection
claude mcp list
```

## Researcher Workflow Scenarios

### Scenario 1: Keyword Research Discovery
**Goal**: Find all documents mentioning "witchcraft" (häxeri) in 17th-century court records.

#### Step 1: Initial Keyword Search
```
Use MCP tool: search_transcribed
Parameters:
- keyword: "häxeri"
- offset: 0
- max_results: 10
- show_context: false
```

**Expected Output**: List of documents with page-level hits, reference codes, and contextual snippets.

#### Step 2: Explore Related Terms
```
Use MCP tool: search_transcribed
Parameters:
- keyword: "trolldom"
- offset: 0
- max_results: 10
```

```
Use MCP tool: search_transcribed
Parameters:
- keyword: "häxa"
- offset: 0
- max_results: 10
```

#### Step 3: Examine Specific Documents
```
Use MCP tool: browse_document
Parameters:
- reference_code: "SE/RA/420422/01" (from search results)
- pages: "15,23,45"
- highlight_term: "häxeri"
```

**Expected Output**: Full transcriptions of specified pages with highlighted search terms.

### Scenario 2: Document Structure Analysis
**Goal**: Understand the organization and scope of a court protocol collection.

#### Step 1: Get Document Overview
```
Use MCP tool: get_document_structure
Parameters:
- reference_code: "SE/RA/420422/01"
- include_manifest_info: true
```

**Expected Output**: Collection metadata, manifest information, total pages, and document hierarchy.

#### Step 2: Browse Sequential Pages
```
Use MCP tool: browse_document
Parameters:
- reference_code: "SE/RA/420422/01"
- pages: "1-5"
```

**Expected Output**: First 5 pages to understand document structure and content style.

### Scenario 3: Comprehensive Topic Research
**Goal**: Research all mentions of "Stockholm" in 17th century documents with full context.

#### Step 1: Comprehensive Search with Context
```
Use MCP tool: search_transcribed
Parameters:
- keyword: "Stockholm"
- offset: 0
- show_context: true
- max_pages_with_context: 5
- context_padding: 1
- max_response_tokens: 20000
```

#### Step 2: Pagination for Complete Coverage
```
Use MCP tool: search_transcribed
Parameters:
- keyword: "Stockholm"
- offset: 10
- show_context: false
- max_results: 10
```

#### Step 3: Deep Dive on Key Documents
```
Use MCP tool: browse_document
Parameters:
- reference_code: [most relevant from results]
- pages: "1-20"
- highlight_term: "Stockholm"
- max_pages: 20
```

### Scenario 4: AI Assistant Research Pattern
**Goal**: AI assistant helps user research historical legal procedures.

#### AI Assistant Workflow:
1. **Initial Query Processing**
   ```
   User: "Help me find information about legal procedures in 17th century Sweden"

   AI uses: search_transcribed("rättegång", offset=0, max_results=15)
   AI uses: search_transcribed("domstol", offset=0, max_results=15)
   AI uses: search_transcribed("protokoll", offset=0, max_results=15)
   ```

2. **Result Analysis and Synthesis**
   - AI analyzes search results for patterns
   - Identifies most relevant documents
   - Cross-references information

3. **Detailed Investigation**
   ```
   AI uses: browse_document(reference_code="SE/RA/420422/01", pages="1-10")
   AI uses: get_document_structure(reference_code="SE/RA/420422/01")
   ```

4. **Contextual Response Generation**
   - AI synthesizes information from multiple sources
   - Provides historical context and interpretation
   - Suggests additional research directions

## Performance Optimization Scenarios

### Scenario 5: Large-Scale Research with Token Management
**Goal**: Research broad topics while staying within AI token limits.

#### Optimized Search Strategy:
```
Use MCP tool: search_transcribed
Parameters:
- keyword: "handel" (trade)
- offset: 0
- show_context: false  # Keep initial response small
- max_results: 20
- max_response_tokens: 8000  # Conservative limit
```

#### Targeted Context Retrieval:
```
Use MCP tool: browse_document
Parameters:
- reference_code: [selected from results]
- pages: "5,12,28"  # Specific pages only
- highlight_term: "handel"
- max_pages: 3  # Limit scope
```

## Error Handling Scenarios

### Scenario 6: Graceful Error Recovery
**Goal**: Handle common errors and provide helpful guidance.

#### No Results Found:
```
Input: search_transcribed("xyz123nonexistent", offset=0)
Expected: Helpful suggestions for alternative search terms
```

#### Invalid Reference Code:
```
Input: browse_document("INVALID/CODE", pages="1")
Expected: Format guidance and suggestions for finding correct codes
```

#### Page Not Available:
```
Input: browse_document("SE/RA/420422/01", pages="999")
Expected: Information about available page ranges
```

## Testing Checklist

### Basic Functionality Tests
- [ ] Server starts successfully in both stdio and HTTP modes
- [ ] All three MCP tools respond to valid requests
- [ ] Search results include proper metadata and formatting
- [ ] Browse functionality loads page content correctly
- [ ] Document structure provides useful navigation information

### Performance Tests
- [ ] Searches complete within 2 seconds for typical queries
- [ ] Token estimation prevents response overflow
- [ ] Pagination works correctly for large result sets
- [ ] Concurrent requests handle properly (up to 10 simultaneous)

### Integration Tests
- [ ] AI assistant can successfully execute multi-step research workflows
- [ ] CLI interface works with same underlying functionality
- [ ] Error messages provide actionable guidance
- [ ] Cache improves response times for repeated queries

### Edge Case Tests
- [ ] Very long keywords (200+ characters) handled gracefully
- [ ] Empty or invalid page ranges handled properly
- [ ] Network timeouts produce helpful error messages
- [ ] Large documents (100+ pages) can be browsed efficiently

## Validation Commands

### Verify Search Functionality
```bash
# Test basic search
curl -X POST http://localhost:8000/mcp/tools/search_transcribed \
  -H "Content-Type: application/json" \
  -d '{"keyword": "Stockholm", "offset": 0}'
```

### Verify Browse Functionality
```bash
# Test document browsing
curl -X POST http://localhost:8000/mcp/tools/browse_document \
  -H "Content-Type: application/json" \
  -d '{"reference_code": "SE/RA/420422/01", "pages": "1-3"}'
```

### Verify Structure Functionality
```bash
# Test structure retrieval
curl -X POST http://localhost:8000/mcp/tools/get_document_structure \
  -H "Content-Type: application/json" \
  -d '{"reference_code": "SE/RA/420422/01"}'
```

## Success Criteria

A successful implementation should demonstrate:

1. **Functional Requirements Coverage**
   - ✅ FR-001: Keyword-based search across millions of documents
   - ✅ FR-002: Search term highlighting in transcriptions
   - ✅ FR-003: Document browsing by reference codes
   - ✅ FR-004: Access to complete transcriptions
   - ✅ FR-005: High-resolution image access via URLs
   - ✅ FR-006: AI tool integration through MCP protocol
   - ✅ FR-007: Command-line interface compatibility
   - ✅ FR-008: API interface for AI system integration
   - ✅ FR-009: Rich metadata in search results
   - ✅ FR-010: Multi-page document navigation
   - ✅ FR-011: Efficient handling of both human and AI requests

2. **Performance Targets**
   - Response times < 2 seconds for typical search queries
   - Support for 100+ concurrent MCP tool calls
   - Token-optimized responses for AI efficiency
   - Proper handling of large document collections

3. **User Experience**
   - Intuitive workflow for researchers and historians
   - Seamless AI assistant integration
   - Helpful error messages and recovery guidance
   - Efficient pagination and navigation
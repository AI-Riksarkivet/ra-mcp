# ra-mcp-search

Search and browse MCP tools for Riksarkivet - provides MCP tools for searching and browsing transcribed historical documents from the Swedish National Archives.

## Installation

```bash
pip install ra-mcp-search
```

## Components

- **mcp**: MCP tools (`search_transcribed`, `browse_document`) and resources
- **services**: Business logic (SearchOperations, BrowseOperations, display services)
- **cli**: CLI commands for search and browse

## MCP Tools

### search_transcribed

Search for keywords in transcribed historical documents. Supports advanced Solr query syntax including wildcards, fuzzy search, Boolean operators, and proximity searches.

### browse_document

Browse specific pages of a document by reference code and view full transcriptions.

## CLI Usage

```bash
# Search for documents
ra search "Stockholm"
ra search "trolldom" --max 50

# Browse specific documents
ra browse "SE/RA/420422/01" --page "5,7,9"
```

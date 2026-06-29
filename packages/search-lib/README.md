# ra-mcp-search-lib

Search domain package for Riksarkivet transcribed documents.

## Overview

Contains the business logic for searching the Swedish National Archives. This is a pure domain package — no MCP or CLI dependency. It provides Pydantic models, an API client, and a search operations layer used by both `ra-mcp-search-mcp` (MCP tools) and `ra-mcp-search-cli` (CLI command).

## Components

- **models.py**: Pydantic models — `SearchRecord` (single result with metadata + transcribed text snippets), `RecordsResponse` (API response wrapper), `SearchResult` (paginated result set)
- **search_client.py**: `SearchClient` — client for the Riksarkivet records API (`https://data.riksarkivet.se/api/records`)
- **search_operations.py**: `SearchOperations` — high-level search orchestration with pagination, filtering, and dedup support
- **config.py**: API URL, default limit (`DEFAULT_LIMIT=50`), and max display (`DEFAULT_MAX_DISPLAY=20`) constants

## Usage

`SearchOperations.search` is async and must be awaited.

```python
import asyncio

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_search_lib.search_operations import SearchOperations


async def main():
    ops = SearchOperations(http_client=HTTPClient())

    result = await ops.search(
        keyword="trolldom",
        transcribed_only=True,
        only_digitised=True,
        offset=0,
        limit=50,
        sort="relevance",
        year_min=1600,
        year_max=1700,
    )

    for record in result.items:
        print(record.metadata.reference_code, record.metadata.title)
        if record.transcribed_text:
            for snippet in record.transcribed_text.snippets:
                print(f"  Page {snippet.pages[0].id}: {snippet.text[:100]}...")


asyncio.run(main())
```

## Search Modes

- **Transcribed text** (`transcribed_only=True`): Full-text search across ~1.6M AI-transcribed pages (court records, 17th-18th century)
- **Metadata** (`transcribed_only=False`): Search 2M+ catalog records by title, name, place, description

## Dependencies

- Internal: `ra-mcp-common`

## Part of ra-mcp

Used by `ra-mcp-search-mcp` (MCP tools) and `ra-mcp-search-cli` (CLI command). See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

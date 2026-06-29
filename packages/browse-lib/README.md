# ra-mcp-browse-lib

Browse domain package for Riksarkivet document pages.

## Overview

Contains the business logic for browsing and retrieving document page transcriptions. This is a pure domain package — no MCP or CLI dependency. It orchestrates three API clients — `ALTOClient`, `IIIFClient`, and `OAIPMHClient` — to assemble full page views with transcribed text, image links, and metadata. Those clients now live in their own workspace packages (`ra-mcp-xml`, `ra-mcp-iiif-lib`, `ra-mcp-oai-pmh-lib`) and are re-exported here for convenience.

## Components

- **models.py**: Pydantic models — `BrowseResult` (full document browse result) and `PageContext` (single page with `full_text`, `image_url`, `alto_url`, `bildvisning_url`). `OAIPMHMetadata` is imported from `ra-mcp-oai-pmh-lib`.
- **browse_operations.py**: `BrowseOperations` — high-level orchestration: resolves a reference code to assembled pages. Constructs `ALTOClient`, `OAIPMHClient`, and `IIIFClient` internally from the injected `HTTPClient`.
- **url_generator.py**: URL construction helpers for bildvisning (image viewer), IIIF images, and ALTO XML
- **utils.py**: Helpers such as `parse_page_range`
- **config.py**: API base URLs and constants

External clients used by `BrowseOperations` (each in its own package):

- `ALTOClient` (`ra-mcp-xml`) — fetches and parses ALTO XML transcriptions into a text layer
- `IIIFClient` (`ra-mcp-iiif-lib`) — resolves IIIF collection manifests to discover page image URLs and identifiers
- `OAIPMHClient` (`ra-mcp-oai-pmh-lib`) — fetches document metadata and derives IIIF manifest IDs via OAI-PMH

## How the Clients Work Together

```
Reference Code (e.g., SE/RA/420422/01)
    |
    v
OAIPMHClient (ra-mcp-oai-pmh-lib) --> metadata + IIIF manifest ID
    |
    v
IIIFClient (ra-mcp-iiif-lib)      --> page list with image IDs
    |
    v
ALTOClient (ra-mcp-xml)           --> transcribed text for each page
    |
    v
BrowseResult                      --> assembled pages with text + image links + metadata
```

## Usage

`BrowseOperations.browse_document` is async and must be awaited.

```python
import asyncio

from ra_mcp_common.http_client import HTTPClient
from ra_mcp_browse_lib.browse_operations import BrowseOperations


async def main():
    ops = BrowseOperations(http_client=HTTPClient())

    result = await ops.browse_document(
        reference_code="SE/RA/420422/01",
        pages="1-5",
        highlight_term="Stockholm",
        max_pages=20,
    )

    for page in result.contexts:
        print(f"Page {page.page_number}: {page.full_text[:100]}...")
        print(f"  Image: {page.image_url}")
        print(f"  Viewer: {page.bildvisning_url}")


asyncio.run(main())
```

## Dependencies

- Internal: `ra-mcp-common`, `ra-mcp-xml`, `ra-mcp-iiif-lib`, `ra-mcp-oai-pmh-lib`

## Part of ra-mcp

Used by `ra-mcp-browse-mcp` (MCP tool) and `ra-mcp-browse-cli` (CLI command). See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

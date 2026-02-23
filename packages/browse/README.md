# ra-mcp-browse

Browse domain package for Riksarkivet document pages.

## Overview

Contains the business logic for browsing and retrieving document page transcriptions. This is a pure domain package — no MCP or CLI dependency. It orchestrates three different API clients (ALTO, IIIF, OAI-PMH) to assemble full page views with transcribed text, image links, and metadata.

## Components

- **models.py**: Pydantic models — `BrowseResult` (full document browse result), `PageContext` (single page with transcription, image URL, ALTO URL), `OAIPMHMetadata` (document-level metadata)
- **clients/alto_client.py**: `ALTOClient` — fetches and parses ALTO XML transcriptions into plain text
- **clients/iiif_client.py**: `IIIFClient` — resolves IIIF collection manifests to discover page image URLs and identifiers
- **clients/oai_pmh_client.py**: `OAIPMHClient` — fetches document metadata and IIIF manifest IDs via OAI-PMH protocol
- **operations/browse_operations.py**: `BrowseOperations` — high-level orchestration: resolves reference code to assembled pages
- **url_generator.py**: URL construction helpers for bildvisaren (image viewer), IIIF images, and ALTO XML
- **config.py**: API base URLs, XML namespaces, and constants

## How the Clients Work Together

```
Reference Code (e.g., SE/RA/420422/01)
    |
    v
OAI-PMH Client --> metadata + IIIF manifest ID
    |
    v
IIIF Client    --> page list with image IDs
    |
    v
ALTO Client    --> transcribed text for each page
    |
    v
BrowseResult   --> assembled pages with text + image links + metadata
```

## Usage

```python
from ra_mcp_common.utils.http_client import HTTPClient
from ra_mcp_browse.browse_operations import BrowseOperations

ops = BrowseOperations(http_client=HTTPClient())

result = ops.browse_document(
    reference_code="SE/RA/420422/01",
    pages="1-5",
    highlight_term="Stockholm",
    max_pages=20,
)

for page in result.contexts:
    print(f"Page {page.page_number}: {page.transcription[:100]}...")
    print(f"  Image: {page.image_url}")
    print(f"  Viewer: {page.bildvisaren_url}")
```

## Dependencies

- Internal: `ra-mcp-common`
- External: `pydantic`

## Part of ra-mcp

Used by `ra-mcp-browse-mcp` (MCP tool) and `ra-mcp-browse-cli` (CLI command). See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

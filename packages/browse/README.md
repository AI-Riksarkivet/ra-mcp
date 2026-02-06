# ra-mcp-browse

Browse domain package for Riksarkivet document pages.

## Components

- **models.py**: Pydantic models (`BrowseResult`, `PageContext`, `OAIPMHMetadata`)
- **clients/alto_client.py**: ALTO XML transcription parser
- **clients/iiif_client.py**: IIIF collection and manifest client
- **clients/oai_pmh_client.py**: OAI-PMH metadata client
- **operations/browse_operations.py**: Browse business logic
- **url_generator.py**: URL construction for bildvisning, IIIF images, and ALTO XML
- **config.py**: API URLs, namespaces, and default constants

## Dependencies

- `ra-mcp-common`: Shared HTTP client

## Part of ra-mcp

Used by `ra-mcp-browse-mcp` (MCP tool) and `ra-mcp-browse-cli` (CLI command).

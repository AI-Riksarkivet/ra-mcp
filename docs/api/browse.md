# Browse

Domain package for browsing and retrieving full page transcriptions from
historical documents (`ra-mcp-browse-lib`, module `ra_mcp_browse_lib`). Depends
on the shared ALTO / IIIF / OAI-PMH client libraries.

## Models

Source: [`packages/browse-lib/src/ra_mcp_browse_lib/models.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/browse-lib/src/ra_mcp_browse_lib/models.py)

Pydantic models `BrowseResult` (a browsed document with its page contexts) and
`PageContext` (a single page's transcription, image links, and metadata).

## Operations

Source: [`packages/browse-lib/src/ra_mcp_browse_lib/browse_operations.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/browse-lib/src/ra_mcp_browse_lib/browse_operations.py)

`BrowseOperations.browse_document(...)` resolves a reference code to a IIIF
manifest, fetches the requested pages' ALTO transcriptions, and assembles a
`BrowseResult`. Traced under `ra_mcp.browse_operations`.

## ALTO Client

Source: [`packages/xml-lib/src/ra_mcp_xml/client.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/xml-lib/src/ra_mcp_xml/client.py)

`ALTOClient.fetch_content(...)` fetches and parses ALTO XML into a `TextLayer`
(`ra-mcp-xml`, module `ra_mcp_xml`).

## IIIF Client

Source: [`packages/iiif-lib/src/ra_mcp_iiif_lib/client.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/iiif-lib/src/ra_mcp_iiif_lib/client.py)

`IIIFClient` retrieves IIIF collections and manifests (`get_collection`,
`fetch_manifest`) from `lbiiif.riksarkivet.se` (`ra-mcp-iiif-lib`).

## OAI-PMH Client

Source: [`packages/oai-pmh-lib/src/ra_mcp_oai_pmh_lib/client.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/oai-pmh-lib/src/ra_mcp_oai_pmh_lib/client.py)

`OAIPMHClient` fetches EAD metadata and resolves manifest identifiers
(`get_metadata`, `extract_manifest_id`) from the OAI-PMH endpoint
(`ra-mcp-oai-pmh-lib`).

## URL Generator

Source: [`packages/browse-lib/src/ra_mcp_browse_lib/url_generator.py`](https://github.com/AI-Riksarkivet/ra-mcp/blob/main/packages/browse-lib/src/ra_mcp_browse_lib/url_generator.py)

Helpers that construct bildvisning, IIIF image, and ALTO URLs from reference
codes and page identifiers.

# ra-mcp-tora-mcp

MCP tools for TORA — geocode historical Swedish places.

## Overview

Thin MCP wrapper around `ra-mcp-tora-lib`. Registers a single FastMCP tool — `search_tora` — that geocodes historical Swedish places by querying TORA (Topografiskt register på Riksarkivet) over its SPARQL endpoint, enriching results with linked historical images and geometrical maps, and returning LLM-friendly formatted output. The tool is registered as a bare name and gets namespaced as `tora:<tool>` when composed into the root server.

## MCP Tools

### `search_tora`

Geocode historical Swedish places using TORA. Returns WGS84 coordinates, parish, municipality, county, and province for 51,000 settlements. Many places include linked historical Suecia Antiqua engravings (1600s) from KB, as well as linked geometrical maps (1630-1700) used as coordinate sources.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | *(required)* | Place name to search for (exact match, e.g. 'Kerstinbo', 'Abbekås') |
| `parish` | str \| None | None | Optional parish name to disambiguate (case-insensitive substring match) |
| `county` | str \| None | None | Optional county/län to disambiguate (case-insensitive substring match) |

## Components

- **tools.py**: FastMCP server setup, instructions, and tool registration
- **tora_tool.py**: `search_tora` tool registration; constructs a `ToraClient` per call
- **formatter.py**: Formats TORA place results for LLM consumption
- **server.py**: Standalone entry point for isolated dev/testing

The underlying `ra-mcp-tora-lib` provides:

- **client.py**: `ToraClient` — async SPARQL client that searches settlements and enriches them with linked images and maps
- **geocode.py**: `geocode()` convenience helper returning a `(lat, lon)` tuple for the best match
- **models.py**: Pydantic models (`ToraPlace`, `ToraImage`, `ToraMapSource`)
- **config.py**: SPARQL endpoint (`https://tora.entryscape.net/store/sparql`) and geocode cache size

## Standalone Usage

```bash
# HTTP transport (default, port 3020)
python -m ra_mcp_tora_mcp.server

# HTTP transport on a custom port
python -m ra_mcp_tora_mcp.server --port 3020

# stdio transport
python -m ra_mcp_tora_mcp.server --stdio
```

## Dependencies

- Internal: `ra-mcp-tora-lib` (uses `httpx` for SPARQL queries)
- External: `fastmcp`

## Part of ra-mcp

Composed into the root server alongside the other dataset modules. The tool is registered as a bare name (`search_tora`) and gets namespaced as `tora:<tool>` in the composed server. See the [docs site](https://ai-riksarkivet.github.io/ra-mcp/) for full project documentation.

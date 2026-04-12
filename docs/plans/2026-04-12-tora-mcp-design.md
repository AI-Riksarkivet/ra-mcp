# TORA MCP — Design

**Date:** 2026-04-12
**Status:** Approved

## Goal

Add a TORA (Topografiskt register på Riksarkivet) MCP module that geocodes historical Swedish place names using Riksarkivet's SPARQL endpoint. Serves two purposes: a standalone MCP tool for place lookups, and a library function other packages can call to enrich their results with coordinates.

## Data source

TORA SPARQL endpoint at `https://tora.entryscape.net/store/sparql`. 51K historical settlement units with WGS84 coordinates, linked to parishes, municipalities, counties, and provinces. No licence explicitly declared — data is queried live (not bulk-ingested) via the public linked open data API.

Key RDF properties:
- `skos:prefLabel` — place name
- `geo:lat` / `geo:long` — WGS84 coordinates (note: comma as decimal separator)
- `tora:modernParish`, `tora:modernMunicipality`, `tora:modernCounty` — administrative links
- `tora:province_name` — historical province
- `dct:coverage` — coordinate accuracy (high/medium/low)
- `rdfs:seeAlso` — wikidata links

## Architecture

Two new packages:

```
ra-mcp-common (HTTPClient)
       ↑
ra-mcp-tora-lib (SPARQL client, geocode, models)
       ↑
ra-mcp-tora-mcp (search_tora tool, formatter)
```

### tora-lib

```
packages/tora-lib/src/ra_mcp_tora_lib/
├── __init__.py          # exports ToraClient, ToraPlace, geocode
├── config.py            # SPARQL_ENDPOINT, cache settings
├── models.py            # ToraPlace (Pydantic BaseModel)
├── client.py            # ToraClient — SPARQL queries via HTTPClient
└── geocode.py           # geocode(name, parish, county) → (lat, lon) | None
```

### tora-mcp

```
packages/tora-mcp/src/ra_mcp_tora_mcp/
├── __init__.py
├── tools.py             # FastMCP("ra-tora-mcp"), register_tora_tool()
├── tora_tool.py         # search_tora MCP tool
├── formatter.py         # format_tora_results()
└── server.py            # standalone dev server
```

## Model

```python
class ToraPlace(BaseModel):
    tora_id: str           # "9809"
    name: str              # "Kerstinbo"
    lat: float             # 60.2506
    lon: float             # 16.9486
    accuracy: str          # "high" / "medium" / "low"
    parish: str            # modern parish name
    municipality: str      # modern municipality
    county: str            # modern county
    province: str          # historical province
    tora_url: str          # "https://data.riksarkivet.se/tora/9809"
    wikidata_url: str      # if available, else ""
```

## SPARQL client

`ToraClient` takes `HTTPClient` in constructor (same pattern as ALTOClient, IIIFClient). Uses `http_client.get_json()` against the SPARQL endpoint with URL-encoded query parameters and `Accept: application/sparql-results+json`.

### search(name, parish=None, county=None) → list[ToraPlace]

SPARQL query matches `skos:prefLabel` on `HistoricalSettlementUnit` type, fetches coordinates and administrative hierarchy via linked resources. Parish and county used as FILTER constraints when provided.

When multiple settlements match, results are ranked by coordinate accuracy (high > medium > low).

### geocode(name, parish=None, county=None) → tuple[float, float] | None

Module-level function, LRU-cached (functools). Calls `ToraClient.search()` internally, returns `(lat, lon)` for the best match or `None`. This is the function other lib packages call.

## Matching strategy

Exact name match on `skos:prefLabel`, with parish and county context for disambiguation. No fuzzy matching — historical place names are consistent within the same era. Multiple matches returned to the LLM to choose from, or disambiguated by parish/county.

## Coordinate parsing

TORA returns coordinates with comma as decimal separator (e.g. `60,2506`). The client replaces commas with dots before parsing to float.

## MCP tool

`search_tora(name, parish=None, county=None)` — returns formatted text:

```
--- Kerstinbo ---
Coordinates: 60.2506, 16.9486 (high accuracy)
Parish: Östervåla
Municipality: Heby kommun
County: Uppsala län
Province: Uppland
TORA: https://data.riksarkivet.se/tora/9809
Wikidata: https://www.wikidata.org/wiki/Q...
```

Multiple matches noted: "3 places match 'Korbo'. Use parish or county to narrow down."

## Error handling

- SPARQL endpoint down → return error message, don't crash
- No matches → "No TORA places found for 'X'"
- Malformed coordinates → handle comma decimal separator

## Testing

- `test_models.py` — ToraPlace construction and validation
- `test_client.py` — mock HTTPClient, verify SPARQL query construction and response parsing
- `test_geocode.py` — cache behavior, disambiguation, no-match returns None
- `test_formatter.py` — output format, multiple results, no results

## Registration

Add to `src/ra_mcp_server/server.py` AVAILABLE_MODULES:

```python
"tora": {
    "server": tora_mcp,
    "description": "Geocode historical Swedish places via TORA",
    "default": True,
},
```

## Future

- Other formatters (Rosenberg, DDS, sjömanshus) can import `geocode()` from tora-lib to enrich results with coordinates
- If licence is confirmed as open, consider bulk-ingesting into Lance for offline/faster lookups

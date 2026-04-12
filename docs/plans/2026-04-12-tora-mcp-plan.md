# TORA MCP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a TORA MCP module that geocodes historical Swedish places via Riksarkivet's SPARQL endpoint, with both an MCP tool and a reusable library function.

**Architecture:** Two new packages (`tora-lib`, `tora-mcp`) following the existing dataset package pattern. `tora-lib` wraps the SPARQL endpoint using HTTPClient; `tora-mcp` exposes a `search_tora` tool. No local data — all queries are live against `https://tora.entryscape.net/store/sparql`.

**Tech Stack:** Pydantic, HTTPClient from ra-mcp-common, FastMCP 3.1.1, functools.lru_cache

---

### Task 1: Scaffold tora-lib package

**Files:**
- Create: `packages/tora-lib/pyproject.toml`
- Create: `packages/tora-lib/src/ra_mcp_tora_lib/__init__.py`
- Create: `packages/tora-lib/src/ra_mcp_tora_lib/config.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ra_mcp_tora_lib"]

[project]
name = "ra-mcp-tora-lib"
version = "0.11.3"
description = "TORA geocoding — historical Swedish places via SPARQL"
requires-python = ">=3.13"
license = "Apache-2.0"
dependencies = [
    "ra-mcp-common",
    "pydantic>=2,<3",
]

[tool.uv.sources]
ra-mcp-common = { workspace = true }
```

**Step 2: Create config.py**

```python
"""Configuration for TORA SPARQL client."""

SPARQL_ENDPOINT = "https://tora.entryscape.net/store/sparql"

# LRU cache size for geocode() — 51K settlements, cache most-queried
GEOCODE_CACHE_SIZE = 4096
```

**Step 3: Create __init__.py**

```python
"""TORA — geocode historical Swedish places via Riksarkivet's SPARQL endpoint."""

from ra_mcp_tora_lib.models import ToraPlace
from ra_mcp_tora_lib.client import ToraClient
from ra_mcp_tora_lib.geocode import geocode

__all__ = ["ToraClient", "ToraPlace", "geocode"]
```

Note: this will fail to import until models.py, client.py, and geocode.py exist. That's fine — we'll create them in the next tasks.

**Step 4: Commit**

```bash
git add packages/tora-lib/
git commit -m "chore(tora): scaffold tora-lib package"
```

---

### Task 2: ToraPlace model + tests

**Files:**
- Create: `packages/tora-lib/src/ra_mcp_tora_lib/models.py`
- Create: `packages/tora-lib/tests/test_models.py`

**Step 1: Write the failing test**

```python
"""Tests for TORA models."""

from ra_mcp_tora_lib.models import ToraPlace


def test_tora_place_construction():
    place = ToraPlace(
        tora_id="9809",
        name="Kerstinbo",
        lat=60.2506,
        lon=16.9486,
        accuracy="high",
        parish="Östervåla",
        municipality="Heby kommun",
        county="Uppsala län",
        province="Uppland",
    )
    assert place.name == "Kerstinbo"
    assert place.lat == 60.2506
    assert place.lon == 16.9486
    assert place.tora_url == "https://data.riksarkivet.se/tora/9809"


def test_tora_place_defaults():
    place = ToraPlace(tora_id="1", name="Test", lat=0.0, lon=0.0)
    assert place.accuracy == ""
    assert place.parish == ""
    assert place.wikidata_url == ""
    assert place.tora_url == "https://data.riksarkivet.se/tora/1"


def test_tora_place_from_sparql_binding():
    """Test parsing from a SPARQL result binding."""
    binding = {
        "place": {"value": "https://data.riksarkivet.se/tora/9809"},
        "name": {"value": "Kerstinbo"},
        "lat": {"value": "60,2506"},
        "long": {"value": "16,9486"},
        "accuracy": {"value": "https://data.riksarkivet.se/tora/coordinateaccuracy/high"},
        "parish": {"value": "Östervåla"},
        "municipality": {"value": "Heby kommun"},
        "county": {"value": "Uppsala län"},
        "province": {"value": "Uppland"},
        "wikidata": {"value": "https://www.wikidata.org/wiki/Q123"},
    }
    place = ToraPlace.from_sparql_binding(binding)
    assert place.tora_id == "9809"
    assert place.lat == 60.2506
    assert place.lon == 16.9486
    assert place.accuracy == "high"
    assert place.wikidata_url == "https://www.wikidata.org/wiki/Q123"


def test_tora_place_from_sparql_binding_missing_optional():
    """Optional fields default to empty string."""
    binding = {
        "place": {"value": "https://data.riksarkivet.se/tora/100"},
        "name": {"value": "Testby"},
        "lat": {"value": "58,0"},
        "long": {"value": "15,0"},
    }
    place = ToraPlace.from_sparql_binding(binding)
    assert place.parish == ""
    assert place.wikidata_url == ""
    assert place.accuracy == ""
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest packages/tora-lib/tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ra_mcp_tora_lib.models'`

**Step 3: Write minimal implementation**

```python
"""Pydantic models for TORA place data."""

from __future__ import annotations

from pydantic import BaseModel, computed_field


def _parse_coord(value: str) -> float:
    """Parse a coordinate string, handling comma as decimal separator."""
    return float(value.replace(",", "."))


def _extract_id(uri: str) -> str:
    """Extract TORA ID from a URI like 'https://data.riksarkivet.se/tora/9809'."""
    return uri.rsplit("/", 1)[-1]


def _extract_accuracy(uri: str) -> str:
    """Extract accuracy level from URI like '.../coordinateaccuracy/high'."""
    if "/" in uri:
        return uri.rsplit("/", 1)[-1]
    return uri


class ToraPlace(BaseModel):
    """A geocoded historical settlement from TORA."""

    tora_id: str
    name: str
    lat: float
    lon: float
    accuracy: str = ""
    parish: str = ""
    municipality: str = ""
    county: str = ""
    province: str = ""
    wikidata_url: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tora_url(self) -> str:
        return f"https://data.riksarkivet.se/tora/{self.tora_id}"

    @classmethod
    def from_sparql_binding(cls, binding: dict) -> ToraPlace:
        """Construct from a SPARQL result binding dict.

        Each key maps to a dict with a 'value' key.
        """
        def _get(key: str) -> str:
            entry = binding.get(key)
            if entry is None:
                return ""
            return entry.get("value", "")

        return cls(
            tora_id=_extract_id(_get("place")),
            name=_get("name"),
            lat=_parse_coord(_get("lat")),
            lon=_parse_coord(_get("long")),
            accuracy=_extract_accuracy(_get("accuracy")),
            parish=_get("parish"),
            municipality=_get("municipality"),
            county=_get("county"),
            province=_get("province"),
            wikidata_url=_get("wikidata"),
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest packages/tora-lib/tests/test_models.py -v`
Expected: all 4 PASS

**Step 5: Commit**

```bash
git add packages/tora-lib/src/ra_mcp_tora_lib/models.py packages/tora-lib/tests/test_models.py
git commit -m "feat(tora): add ToraPlace model with SPARQL binding parser"
```

---

### Task 3: ToraClient SPARQL client + tests

**Files:**
- Create: `packages/tora-lib/src/ra_mcp_tora_lib/client.py`
- Create: `packages/tora-lib/tests/test_client.py`

**Step 1: Write the failing test**

Test the client by mocking HTTPClient. The test verifies:
- Correct SPARQL query construction
- Response parsing into ToraPlace objects
- Parish/county filtering via SPARQL FILTER clauses

```python
"""Tests for TORA SPARQL client."""

import pytest
from unittest.mock import AsyncMock

from ra_mcp_tora_lib.client import ToraClient
from ra_mcp_tora_lib.models import ToraPlace


def _mock_sparql_response(bindings: list[dict]) -> dict:
    """Build a SPARQL JSON response."""
    return {"results": {"bindings": bindings}}


def _kerstinbo_binding() -> dict:
    return {
        "place": {"value": "https://data.riksarkivet.se/tora/9809"},
        "name": {"value": "Kerstinbo"},
        "lat": {"value": "60,2506"},
        "long": {"value": "16,9486"},
        "accuracy": {"value": "https://data.riksarkivet.se/tora/coordinateaccuracy/high"},
        "parish": {"value": "Östervåla"},
        "municipality": {"value": "Heby kommun"},
        "county": {"value": "Uppsala län"},
        "province": {"value": "Uppland"},
    }


@pytest.fixture
def mock_http():
    http = AsyncMock()
    http.get_json = AsyncMock()
    return http


async def test_search_returns_places(mock_http):
    mock_http.get_json.return_value = _mock_sparql_response([_kerstinbo_binding()])
    client = ToraClient(http_client=mock_http)

    results = await client.search("Kerstinbo")

    assert len(results) == 1
    assert results[0].name == "Kerstinbo"
    assert results[0].lat == 60.2506
    mock_http.get_json.assert_called_once()


async def test_search_empty_results(mock_http):
    mock_http.get_json.return_value = _mock_sparql_response([])
    client = ToraClient(http_client=mock_http)

    results = await client.search("Nonexistent")

    assert results == []


async def test_search_with_parish_filter(mock_http):
    mock_http.get_json.return_value = _mock_sparql_response([_kerstinbo_binding()])
    client = ToraClient(http_client=mock_http)

    results = await client.search("Kerstinbo", parish="Östervåla")

    assert len(results) == 1
    # Verify the SPARQL query included a parish filter
    call_args = mock_http.get_json.call_args
    query_url = call_args[0][0]
    assert "Östervåla" in query_url or "parish" in str(call_args)


async def test_search_endpoint_down(mock_http):
    mock_http.get_json.return_value = None
    client = ToraClient(http_client=mock_http)

    results = await client.search("Kerstinbo")

    assert results == []


async def test_search_deduplicates(mock_http):
    """TORA often returns duplicate bindings — client should deduplicate."""
    binding = _kerstinbo_binding()
    mock_http.get_json.return_value = _mock_sparql_response([binding, binding])
    client = ToraClient(http_client=mock_http)

    results = await client.search("Kerstinbo")

    assert len(results) == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest packages/tora-lib/tests/test_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write implementation**

```python
"""TORA SPARQL client — queries historical settlements from Riksarkivet."""

from __future__ import annotations

import logging
import urllib.parse

from ra_mcp_common.http_client import HTTPClient, default_http_client

from .config import SPARQL_ENDPOINT
from .models import ToraPlace


logger = logging.getLogger("ra_mcp.tora.client")


def _build_search_query(name: str, parish: str | None = None, county: str | None = None) -> str:
    """Build SPARQL query to find settlements by name with optional filters."""
    filters = [f'FILTER(LCASE(?name) = LCASE("{name}"))']
    if parish:
        filters.append(f'FILTER(CONTAINS(LCASE(?parish), LCASE("{parish}")))')
    if county:
        filters.append(f'FILTER(CONTAINS(LCASE(?county), LCASE("{county}")))')

    filter_block = "\n    ".join(filters)

    return f"""
PREFIX tora: <https://data.riksarkivet.se/tora/schema/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?place ?name ?lat ?long ?accuracy ?parish ?municipality ?county ?province ?wikidata WHERE {{
  ?place a tora:HistoricalSettlementUnit ;
         skos:prefLabel ?name ;
         geo:lat ?lat ;
         geo:long ?long .
  {filter_block}
  OPTIONAL {{ ?place dct:coverage ?accuracy }}
  OPTIONAL {{ ?place tora:modernParish ?parishUri . ?parishUri skos:prefLabel ?parish }}
  OPTIONAL {{ ?place tora:modernMunicipality ?munUri . ?munUri skos:prefLabel ?municipality }}
  OPTIONAL {{ ?place tora:modernCounty ?countyUri . ?countyUri skos:prefLabel ?county }}
  OPTIONAL {{ ?place tora:province_name ?province }}
  OPTIONAL {{ ?place rdfs:seeAlso ?wikidata . FILTER(CONTAINS(STR(?wikidata), "wikidata")) }}
}} LIMIT 20
"""


class ToraClient:
    """Client for querying TORA settlements via SPARQL."""

    def __init__(self, http_client: HTTPClient = default_http_client) -> None:
        self._http = http_client

    async def search(
        self,
        name: str,
        parish: str | None = None,
        county: str | None = None,
    ) -> list[ToraPlace]:
        """Search for settlements by name, optionally filtered by parish/county."""
        query = _build_search_query(name, parish, county)
        url = f"{SPARQL_ENDPOINT}?query={urllib.parse.quote(query)}"

        try:
            data = await self._http.get_json(url, headers={"Accept": "application/sparql-results+json"})
        except Exception as e:
            logger.error("TORA SPARQL query failed: %s", e)
            return []

        if not data:
            return []

        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return []

        # Deduplicate by tora_id (SPARQL often returns duplicate rows)
        seen: set[str] = set()
        places: list[ToraPlace] = []
        for binding in bindings:
            try:
                place = ToraPlace.from_sparql_binding(binding)
            except Exception as e:
                logger.warning("Failed to parse TORA binding: %s", e)
                continue
            if place.tora_id not in seen:
                seen.add(place.tora_id)
                places.append(place)

        # Sort by accuracy: high > medium > low > empty
        accuracy_order = {"high": 0, "medium": 1, "low": 2, "": 3}
        places.sort(key=lambda p: accuracy_order.get(p.accuracy, 3))

        return places
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest packages/tora-lib/tests/test_client.py -v`
Expected: all 5 PASS

**Step 5: Commit**

```bash
git add packages/tora-lib/src/ra_mcp_tora_lib/client.py packages/tora-lib/tests/test_client.py
git commit -m "feat(tora): add ToraClient SPARQL client"
```

---

### Task 4: geocode() function + tests

**Files:**
- Create: `packages/tora-lib/src/ra_mcp_tora_lib/geocode.py`
- Create: `packages/tora-lib/tests/test_geocode.py`

**Step 1: Write the failing test**

```python
"""Tests for the geocode convenience function."""

import pytest
from unittest.mock import AsyncMock, patch

from ra_mcp_tora_lib.geocode import geocode
from ra_mcp_tora_lib.models import ToraPlace


def _make_place(**overrides) -> ToraPlace:
    defaults = dict(tora_id="1", name="Test", lat=60.0, lon=16.0, accuracy="high")
    defaults.update(overrides)
    return ToraPlace(**defaults)


@patch("ra_mcp_tora_lib.geocode.ToraClient")
async def test_geocode_returns_coordinates(mock_cls):
    client = AsyncMock()
    client.search.return_value = [_make_place(lat=60.25, lon=16.95)]
    mock_cls.return_value = client

    result = await geocode("Kerstinbo")

    assert result == (60.25, 16.95)


@patch("ra_mcp_tora_lib.geocode.ToraClient")
async def test_geocode_returns_none_when_not_found(mock_cls):
    client = AsyncMock()
    client.search.return_value = []
    mock_cls.return_value = client

    result = await geocode("Nonexistent")

    assert result is None


@patch("ra_mcp_tora_lib.geocode.ToraClient")
async def test_geocode_passes_parish_and_county(mock_cls):
    client = AsyncMock()
    client.search.return_value = [_make_place()]
    mock_cls.return_value = client

    await geocode("Korbo", parish="Östervåla", county="Uppsala")

    client.search.assert_called_once_with("Korbo", parish="Östervåla", county="Uppsala")
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest packages/tora-lib/tests/test_geocode.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
"""Convenience geocode function for looking up coordinates by place name."""

from __future__ import annotations

from ra_mcp_common.http_client import default_http_client

from .client import ToraClient


async def geocode(
    name: str,
    parish: str | None = None,
    county: str | None = None,
) -> tuple[float, float] | None:
    """Look up coordinates for a historical Swedish place name.

    Args:
        name: Place name to search for (exact match).
        parish: Optional parish name to disambiguate.
        county: Optional county name to disambiguate.

    Returns:
        (lat, lon) tuple for the best match, or None if not found.
    """
    client = ToraClient(http_client=default_http_client)
    places = await client.search(name, parish=parish, county=county)
    if not places:
        return None
    return (places[0].lat, places[0].lon)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest packages/tora-lib/tests/test_geocode.py -v`
Expected: all 3 PASS

**Step 5: Run all tora-lib tests**

Run: `uv run pytest packages/tora-lib/tests/ -v`
Expected: all 12 PASS

**Step 6: Commit**

```bash
git add packages/tora-lib/src/ra_mcp_tora_lib/geocode.py packages/tora-lib/tests/test_geocode.py
git commit -m "feat(tora): add geocode() convenience function"
```

---

### Task 5: Scaffold tora-mcp package

**Files:**
- Create: `packages/tora-mcp/pyproject.toml`
- Create: `packages/tora-mcp/src/ra_mcp_tora_mcp/__init__.py`
- Create: `packages/tora-mcp/src/ra_mcp_tora_mcp/tools.py`
- Create: `packages/tora-mcp/src/ra_mcp_tora_mcp/server.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ra_mcp_tora_mcp"]

[project]
name = "ra-mcp-tora-mcp"
version = "0.11.3"
description = "MCP tools for TORA — geocode historical Swedish places"
requires-python = ">=3.13"
license = "Apache-2.0"
dependencies = [
    "ra-mcp-tora-lib",
    "fastmcp==3.1.1",
]

[tool.uv.sources]
ra-mcp-tora-lib = { workspace = true }
```

**Step 2: Create __init__.py**

```python
from ra_mcp_tora_mcp.tools import tora_mcp

__all__ = ["tora_mcp"]
```

**Step 3: Create tools.py**

```python
"""FastMCP server definition for TORA geocoding tools."""

from fastmcp import FastMCP

from .tora_tool import register_tora_tool


tora_mcp = FastMCP(
    name="ra-tora-mcp",
    instructions=(
        "Geocode historical Swedish places using TORA (Topografiskt register på Riksarkivet). "
        "51,000 settlements with WGS84 coordinates, linked to parishes, municipalities, and counties. "
        "Use for looking up coordinates and administrative context of historical Swedish places."
    ),
)

register_tora_tool(tora_mcp)
```

Note: this will fail until tora_tool.py exists.

**Step 4: Create server.py**

```python
"""Standalone dev server for TORA MCP."""

import argparse
import os

from .tools import tora_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="TORA MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3020")))
    args = parser.parse_args()
    if args.stdio:
        tora_mcp.run(transport="stdio")
    else:
        tora_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
```

**Step 5: Commit**

```bash
git add packages/tora-mcp/
git commit -m "chore(tora): scaffold tora-mcp package"
```

---

### Task 6: Formatter + MCP tool + tests

**Files:**
- Create: `packages/tora-mcp/src/ra_mcp_tora_mcp/formatter.py`
- Create: `packages/tora-mcp/src/ra_mcp_tora_mcp/tora_tool.py`
- Create: `packages/tora-mcp/tests/test_tora_formatter.py`
- Create: `packages/tora-mcp/tests/test_tools.py`

**Step 1: Write formatter test**

```python
"""Tests for TORA formatter."""

from ra_mcp_tora_lib.models import ToraPlace
from ra_mcp_tora_mcp.formatter import format_tora_results


def _make_place(**overrides) -> ToraPlace:
    defaults = dict(
        tora_id="9809",
        name="Kerstinbo",
        lat=60.2506,
        lon=16.9486,
        accuracy="high",
        parish="Östervåla",
        municipality="Heby kommun",
        county="Uppsala län",
        province="Uppland",
    )
    defaults.update(overrides)
    return ToraPlace(**defaults)


def test_format_single_result():
    text = format_tora_results("Kerstinbo", [_make_place()])
    assert "Kerstinbo" in text
    assert "60.2506" in text
    assert "16.9486" in text
    assert "Östervåla" in text
    assert "Uppsala län" in text
    assert "https://data.riksarkivet.se/tora/9809" in text


def test_format_no_results():
    text = format_tora_results("Nonexistent", [])
    assert "No TORA places found" in text


def test_format_multiple_results():
    places = [
        _make_place(tora_id="1", name="Korbo", parish="A"),
        _make_place(tora_id="2", name="Korbo", parish="B"),
    ]
    text = format_tora_results("Korbo", places)
    assert "2 places" in text


def test_format_includes_wikidata_when_present():
    text = format_tora_results("Test", [_make_place(wikidata_url="https://www.wikidata.org/wiki/Q123")])
    assert "wikidata.org" in text


def test_format_omits_wikidata_when_empty():
    text = format_tora_results("Test", [_make_place(wikidata_url="")])
    assert "Wikidata" not in text
```

**Step 2: Write formatter**

```python
"""Plain-text formatter for TORA search results."""

from __future__ import annotations

from ra_mcp_tora_lib.models import ToraPlace


def _append_if(lines: list[str], label: str, value: str) -> None:
    if value:
        lines.append(f"{label}: {value}")


def _format_place(place: ToraPlace, lines: list[str]) -> None:
    lines.append(f"--- {place.name} ---")

    accuracy_note = f" ({place.accuracy} accuracy)" if place.accuracy else ""
    lines.append(f"Coordinates: {place.lat}, {place.lon}{accuracy_note}")

    _append_if(lines, "Parish", place.parish)
    _append_if(lines, "Municipality", place.municipality)
    _append_if(lines, "County", place.county)
    _append_if(lines, "Province", place.province)
    lines.append(f"TORA: {place.tora_url}")
    _append_if(lines, "Wikidata", place.wikidata_url)
    lines.append("")


def format_tora_results(query: str, places: list[ToraPlace]) -> str:
    if not places:
        return f"No TORA places found for '{query}'."

    lines: list[str] = []

    if len(places) > 1:
        lines.append(f"TORA: {len(places)} places match '{query}'. Use parish or county to narrow down.")
    else:
        lines.append(f"TORA result for '{query}':")
    lines.append("")

    for place in places:
        _format_place(place, lines)

    return "\n".join(lines)
```

**Step 3: Run formatter tests**

Run: `uv run pytest packages/tora-mcp/tests/test_tora_formatter.py -v`
Expected: all 5 PASS

**Step 4: Write tora_tool.py**

```python
"""MCP tool for searching TORA historical places."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_tora_lib.client import ToraClient
from ra_mcp_common.http_client import default_http_client

from .formatter import format_tora_results


logger = logging.getLogger("ra_mcp.tora.tora_tool")


def register_tora_tool(mcp) -> None:
    """Register the search_tora MCP tool."""

    @mcp.tool(
        name="search_tora",
        tags={"tora", "geography", "geocode", "places", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Geocode historical Swedish places using TORA (Topografiskt register på Riksarkivet). "
            "Returns WGS84 coordinates, parish, municipality, county, and province for 51,000 settlements. "
            "Use to find the location of a historical Swedish place, village, or settlement. "
            "Optionally filter by parish or county to disambiguate common place names."
        ),
    )
    async def search_tora(
        name: Annotated[
            str,
            Field(description="Place name to search for (exact match, e.g. 'Kerstinbo', 'Abbekås')."),
        ],
        parish: Annotated[
            str | None,
            Field(description="Optional parish name to disambiguate (case-insensitive substring match)."),
        ] = None,
        county: Annotated[
            str | None,
            Field(description="Optional county/län to disambiguate (case-insensitive substring match, e.g. 'Uppsala', 'Malmöhus')."),
        ] = None,
    ) -> str:
        """Search for a historical Swedish place and get its coordinates."""
        if not name or not name.strip():
            return "Error: name must not be empty."

        logger.info("search_tora called with name='%s', parish=%s, county=%s", name, parish, county)

        try:
            client = ToraClient(http_client=default_http_client)
            places = await client.search(name.strip(), parish=parish, county=county)
            return format_tora_results(name, places)

        except Exception as exc:
            logger.error("search_tora failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: TORA search failed — {exc!s}"
```

**Step 5: Write basic tool test**

```python
"""Basic tests for the tora-mcp package."""


def test_tora_mcp_has_name():
    from ra_mcp_tora_mcp.tools import tora_mcp

    assert tora_mcp.name == "ra-tora-mcp"
```

**Step 6: Run all tora-mcp tests**

Run: `uv run pytest packages/tora-mcp/tests/ -v`
Expected: all 6 PASS

**Step 7: Commit**

```bash
git add packages/tora-mcp/src/ra_mcp_tora_mcp/formatter.py packages/tora-mcp/src/ra_mcp_tora_mcp/tora_tool.py packages/tora-mcp/tests/
git commit -m "feat(tora): add search_tora MCP tool and formatter"
```

---

### Task 7: Register in root server + dependencies

**Files:**
- Modify: `src/ra_mcp_server/server.py` (add tora module registration)
- Modify: `pyproject.toml` (add tora dependencies and workspace sources)

**Step 1: Add tora to server.py**

Add after the rosenberg block (around line 130):

```python
# tora-mcp is optional
try:
    from ra_mcp_tora_mcp import tora_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["tora"] = {
        "server": tora_mcp,
        "description": "Geocode historical Swedish places via TORA (51K settlements with coordinates)",
        "default": True,
    }
except ImportError:
    pass
```

Also add to the TOOL SELECTION instructions in the server instructions string:
```
- Geocode historical place → tora:search_tora with name, optional parish/county
```

**Step 2: Add to pyproject.toml dependencies**

Add `"ra-mcp-tora-mcp"` to the `dependencies` list.
Add `tora = ["ra-mcp-tora-mcp"]` to the `[project.optional-dependencies]` section.
Add workspace sources:
```toml
ra-mcp-tora-lib = { workspace = true }
ra-mcp-tora-mcp = { workspace = true }
```

**Step 3: Run uv sync**

Run: `uv sync`
Expected: workspace packages resolve successfully

**Step 4: Verify server starts**

Run: `uv run ra serve --port 7860 &` (or check the existing server)
Verify tora module loads in the module list.

**Step 5: Commit**

```bash
git add src/ra_mcp_server/server.py pyproject.toml
git commit -m "feat(tora): register tora module in root server"
```

---

### Task 8: Integration test — live SPARQL query

**Files:**
- Create: `packages/tora-lib/tests/test_integration.py`

This test hits the real SPARQL endpoint. Mark it so it can be skipped in CI.

**Step 1: Write integration test**

```python
"""Integration tests against live TORA SPARQL endpoint.

These tests require network access. Skip with: pytest -m "not integration"
"""

import pytest

from ra_mcp_tora_lib.client import ToraClient
from ra_mcp_tora_lib.geocode import geocode
from ra_mcp_common.http_client import default_http_client


pytestmark = pytest.mark.integration


async def test_live_search_kerstinbo():
    """Kerstinbo should be findable and have coordinates."""
    client = ToraClient(http_client=default_http_client)
    results = await client.search("Kerstinbo")

    assert len(results) >= 1
    place = results[0]
    assert place.name == "Kerstinbo"
    assert 59 < place.lat < 61  # roughly Uppsala county
    assert 16 < place.lon < 18


async def test_live_search_abbekas():
    """Abbekås — a coastal village in Skåne."""
    client = ToraClient(http_client=default_http_client)
    results = await client.search("Abbekås")

    assert len(results) >= 1
    assert 55 < results[0].lat < 56  # southern Sweden


async def test_live_geocode():
    """geocode() should return a tuple."""
    result = await geocode("Kerstinbo")

    assert result is not None
    lat, lon = result
    assert 59 < lat < 61


async def test_live_geocode_not_found():
    result = await geocode("Xyzzyplansen")

    assert result is None
```

**Step 2: Run integration tests**

Run: `uv run pytest packages/tora-lib/tests/test_integration.py -v -m integration`
Expected: all 4 PASS (requires network)

**Step 3: Commit**

```bash
git add packages/tora-lib/tests/test_integration.py
git commit -m "test(tora): add integration tests against live SPARQL endpoint"
```

---

### Task 9: Run full test suite + verify

**Step 1: Run all tora tests**

Run: `uv run pytest packages/tora-lib/tests/ packages/tora-mcp/tests/ -v`
Expected: all tests PASS

**Step 2: Run ruff checks**

Run: `uv run ruff check packages/tora-lib/ packages/tora-mcp/`
Expected: no errors

Run: `uv run ruff format --check packages/tora-lib/ packages/tora-mcp/`
Expected: no changes needed

**Step 3: Verify the existing test suite still passes**

Run: `uv run pytest --ignore=packages/viewer-mcp/tests/test_parser.py -x -q`
Expected: no regressions

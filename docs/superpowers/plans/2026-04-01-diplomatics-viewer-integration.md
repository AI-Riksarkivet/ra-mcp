# Diplomatics → Viewer Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `view_sdhk` and `view_mpo` tools that look up a record by ID from LanceDB, format rich metadata for the viewer info panel, and open the document in the interactive viewer — all in one call. Also add a `document_info` parameter to `view_manifest` for ad-hoc use.

**Architecture:** Three changes: (1) Add `get_by_id` methods to `DiplomaticsSearch` in diplomatics-lib for single-record lookup. (2) Add `format_sdhk_info` / `format_mpo_info` functions in diplomatics-mcp that produce markdown for the viewer's info panel. (3) Register `view_sdhk` / `view_mpo` tools in diplomatics-mcp that call the lookup, format metadata, resolve the IIIF manifest via `manifest_resolve_document`, and return a `ToolResult` with `ViewerState`. Also add optional `document_info` param to `view_manifest`.

**Tech Stack:** LanceDB (existing), FastMCP `ToolResult` + `AppConfig`, existing `manifest_resolve_document` from viewer-mcp, `ViewerState` model.

---

## File Structure

### Modified files

```
packages/diplomatics-lib/src/ra_mcp_diplomatics_lib/search_operations.py
  — Add get_sdhk_by_id() and get_mpo_by_id() methods to DiplomaticsSearch

packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/formatter.py
  — Add format_sdhk_info() and format_mpo_info() that return markdown for ViewerState.document_info

packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/tools.py
  — Register view_sdhk and view_mpo tools, add viewer-mcp dependency import

packages/diplomatics-mcp/pyproject.toml
  — Add ra-mcp-viewer-mcp dependency (needed for manifest_resolve_document, ViewerState, put_state)

packages/viewer-mcp/src/ra_mcp_viewer_mcp/tools.py
  — Add optional document_info parameter to view_manifest
```

### New files

```
packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/view_sdhk_tool.py
  — view_sdhk MCP tool

packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/view_mpo_tool.py
  — view_mpo MCP tool

packages/diplomatics-lib/tests/test_get_by_id.py
  — Tests for get_sdhk_by_id / get_mpo_by_id

packages/diplomatics-mcp/tests/test_formatter_info.py
  — Tests for format_sdhk_info / format_mpo_info
```

---

### Task 1: Add get_by_id methods to DiplomaticsSearch

**Files:**
- Create: `packages/diplomatics-lib/tests/test_get_by_id.py`
- Modify: `packages/diplomatics-lib/src/ra_mcp_diplomatics_lib/search_operations.py`

- [ ] **Step 1: Write the failing tests**

Create `packages/diplomatics-lib/tests/test_get_by_id.py`:

```python
"""Tests for single-record lookup by ID."""

import pytest

from ra_mcp_diplomatics_lib.search_operations import DiplomaticsSearch


class FakeTable:
    """Minimal fake that mimics LanceDB table.search() and table.to_pandas()."""

    def __init__(self, rows: list[dict]):
        self._rows = rows

    def search(self, query, query_type="fts"):
        # Not used by get_by_id
        raise NotImplementedError

    def to_list(self):
        return self._rows

    def filter(self, expr):
        """LanceDB filter returns a query builder with .to_list()."""
        return _FilteredQuery(self._rows, expr)


class _FilteredQuery:
    def __init__(self, rows, expr):
        self._rows = rows
        self._expr = expr

    def limit(self, n):
        self._limit = n
        return self

    def to_list(self):
        # Simple id-based filtering for test purposes
        # Expression is like "id = 123"
        target_id = int(self._expr.split("=")[1].strip())
        return [r for r in self._rows if r.get("id") == target_id][:self._limit]


class FakeDB:
    def __init__(self, tables: dict[str, FakeTable]):
        self._tables = tables

    def open_table(self, name):
        return self._tables[name]


SDHK_ROW = {
    "id": 85,
    "title": "SDHK nr 85",
    "author": "Knut Eriksson",
    "date": "11670000",
    "place": "Linköping",
    "language": "latin",
    "summary": "King Knut confirms privileges.",
    "manifest_url": "https://lbiiif.riksarkivet.se/sdhk!85/manifest",
    "has_manifest": True,
    "has_transcription": True,
}

MPO_ROW = {
    "id": 1,
    "manuscript_type": "Missale",
    "category": "Lit",
    "institution": "RA",
    "dating": "14. Jh.",
    "origin_place": "Skandinavien?",
    "content": "1r-2v Ordo missae.",
    "manifest_url": "https://lbiiif.riksarkivet.se/arkis!R1000001/manifest",
}


def test_get_sdhk_by_id_found():
    db = FakeDB({"sdhk": FakeTable([SDHK_ROW])})
    searcher = DiplomaticsSearch(db)
    row = searcher.get_sdhk_by_id(85)
    assert row is not None
    assert row["id"] == 85
    assert row["author"] == "Knut Eriksson"


def test_get_sdhk_by_id_not_found():
    db = FakeDB({"sdhk": FakeTable([SDHK_ROW])})
    searcher = DiplomaticsSearch(db)
    row = searcher.get_sdhk_by_id(99999)
    assert row is None


def test_get_mpo_by_id_found():
    db = FakeDB({"mpo": FakeTable([MPO_ROW])})
    searcher = DiplomaticsSearch(db)
    row = searcher.get_mpo_by_id(1)
    assert row is not None
    assert row["manuscript_type"] == "Missale"


def test_get_mpo_by_id_not_found():
    db = FakeDB({"mpo": FakeTable([MPO_ROW])})
    searcher = DiplomaticsSearch(db)
    row = searcher.get_mpo_by_id(99999)
    assert row is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/morgan/ra-mcp && uv run pytest packages/diplomatics-lib/tests/test_get_by_id.py -v`
Expected: FAIL with `AttributeError: 'DiplomaticsSearch' object has no attribute 'get_sdhk_by_id'`

- [ ] **Step 3: Implement get_by_id methods**

Add to `packages/diplomatics-lib/src/ra_mcp_diplomatics_lib/search_operations.py`, inside the `DiplomaticsSearch` class, after `search_mpo`:

```python
    def get_sdhk_by_id(self, sdhk_id: int) -> dict | None:
        """Look up a single SDHK record by ID.

        Returns the record dict or None if not found.
        """
        table = self._db.open_table(SDHK_TABLE)
        rows = table.filter(f"id = {sdhk_id}").limit(1).to_list()
        return rows[0] if rows else None

    def get_mpo_by_id(self, mpo_id: int) -> dict | None:
        """Look up a single MPO record by ID.

        Returns the record dict or None if not found.
        """
        table = self._db.open_table(MPO_TABLE)
        rows = table.filter(f"id = {mpo_id}").limit(1).to_list()
        return rows[0] if rows else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/morgan/ra-mcp && uv run pytest packages/diplomatics-lib/tests/test_get_by_id.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add packages/diplomatics-lib/src/ra_mcp_diplomatics_lib/search_operations.py packages/diplomatics-lib/tests/test_get_by_id.py
git commit -m "feat(diplomatics-lib): add get_sdhk_by_id and get_mpo_by_id lookup methods"
```

---

### Task 2: Add info panel formatters

**Files:**
- Create: `packages/diplomatics-mcp/tests/test_formatter_info.py`
- Modify: `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/formatter.py`

- [ ] **Step 1: Write the failing tests**

Create `packages/diplomatics-mcp/tests/test_formatter_info.py`:

```python
"""Tests for info-panel markdown formatters."""

from ra_mcp_diplomatics_mcp.formatter import format_mpo_info, format_sdhk_info


def test_format_sdhk_info_full():
    row = {
        "id": 85,
        "title": "SDHK nr 85",
        "author": "Knut Eriksson",
        "date": "11670000",
        "place": "Linköping",
        "language": "latin",
        "summary": "King Knut confirms privileges.",
        "edition": "Omnibus presentes literas inspecturis...",
        "seals": "Sigillum regis",
        "printed": "DS I 60",
    }
    md = format_sdhk_info(row)
    assert "## SDHK 85" in md
    assert "**Author:** Knut Eriksson" in md
    assert "**Date:** 11670000" in md
    assert "**Place:** Linköping" in md
    assert "**Language:** latin" in md
    assert "King Knut confirms privileges." in md
    assert "Omnibus presentes literas inspecturis..." in md
    assert "Sigillum regis" in md
    assert "DS I 60" in md


def test_format_sdhk_info_minimal():
    row = {"id": 1, "title": "", "author": "", "date": "", "summary": ""}
    md = format_sdhk_info(row)
    assert "## SDHK 1" in md
    # No empty fields rendered
    assert "**Author:**" not in md


def test_format_mpo_info_full():
    row = {
        "id": 42,
        "manuscript_type": "Missale",
        "category": "Lit",
        "title": "Missale Lundense",
        "author": "Unknown",
        "dating": "14. Jh.",
        "origin_place": "Skandinavien?",
        "institution": "RA",
        "collection": "Östergötlands handlingar",
        "script": "Textualis",
        "material": "Pergament",
        "notation": "Quadr",
        "decoration": "Rote und blaue Lombarden.",
        "content": "1r-2v Ordo missae.",
        "format_size": "40.5 x 28.5",
        "damage": "Beschnitten am Rand.",
    }
    md = format_mpo_info(row)
    assert "## MPO 42" in md
    assert "**Type:** Missale" in md
    assert "**Category:** Lit" in md
    assert "**Dating:** 14. Jh." in md
    assert "**Script:** Textualis" in md
    assert "**Material:** Pergament" in md
    assert "Rote und blaue Lombarden." in md
    assert "1r-2v Ordo missae." in md


def test_format_mpo_info_minimal():
    row = {"id": 99, "manuscript_type": "", "category": ""}
    md = format_mpo_info(row)
    assert "## MPO 99" in md
    assert "**Type:**" not in md
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/morgan/ra-mcp && uv run pytest packages/diplomatics-mcp/tests/test_formatter_info.py -v`
Expected: FAIL with `ImportError: cannot import name 'format_sdhk_info'`

- [ ] **Step 3: Implement formatters**

Add to the end of `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/formatter.py`:

```python
def format_sdhk_info(row: dict) -> str:
    """Format an SDHK record as markdown for the viewer info panel."""
    sdhk_id = row.get("id", "?")
    lines: list[str] = [f"## SDHK {sdhk_id}"]

    title = row.get("title", "")
    if title:
        lines.append(f"*{title}*")
    lines.append("")

    for label, key in [
        ("Author", "author"),
        ("Date", "date"),
        ("Place", "place"),
        ("Language", "language"),
        ("Printed", "printed"),
    ]:
        val = row.get(key, "")
        if val:
            lines.append(f"**{label}:** {val}")

    summary = row.get("summary", "")
    if summary:
        lines.append("")
        lines.append("### Summary")
        lines.append(summary)

    edition = row.get("edition", "")
    if edition:
        truncated = edition[:1000] + "..." if len(edition) > 1000 else edition
        lines.append("")
        lines.append("### Edition")
        lines.append(truncated)

    seals = row.get("seals", "")
    if seals:
        lines.append("")
        lines.append("### Seals")
        lines.append(seals)

    return "\n".join(lines)


def format_mpo_info(row: dict) -> str:
    """Format an MPO record as markdown for the viewer info panel."""
    mpo_id = row.get("id", "?")
    lines: list[str] = [f"## MPO {mpo_id}"]

    manuscript_type = row.get("manuscript_type", "")
    if manuscript_type:
        lines.append(f"*{manuscript_type}*")
    lines.append("")

    for label, key in [
        ("Type", "manuscript_type"),
        ("Category", "category"),
        ("Title", "title"),
        ("Author", "author"),
        ("Dating", "dating"),
        ("Origin", "origin_place"),
        ("Institution", "institution"),
        ("Collection", "collection"),
        ("Script", "script"),
        ("Material", "material"),
        ("Notation", "notation"),
        ("Size", "format_size"),
    ]:
        val = row.get(key, "")
        if val:
            lines.append(f"**{label}:** {val}")

    decoration = row.get("decoration", "")
    if decoration:
        lines.append("")
        lines.append("### Decoration")
        lines.append(decoration)

    content = row.get("content", "")
    if content:
        lines.append("")
        lines.append("### Content")
        lines.append(content)

    damage = row.get("damage", "")
    if damage:
        lines.append("")
        lines.append("### Damage")
        lines.append(damage)

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/morgan/ra-mcp && uv run pytest packages/diplomatics-mcp/tests/test_formatter_info.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/formatter.py packages/diplomatics-mcp/tests/test_formatter_info.py
git commit -m "feat(diplomatics-mcp): add info panel markdown formatters for SDHK and MPO"
```

---

### Task 3: Add document_info parameter to view_manifest

**Files:**
- Modify: `packages/viewer-mcp/src/ra_mcp_viewer_mcp/tools.py:145-184`

- [ ] **Step 1: Add document_info parameter to view_manifest**

In `packages/viewer-mcp/src/ra_mcp_viewer_mcp/tools.py`, change the `view_manifest` function signature and body. Replace the existing function (lines 145-184):

```python
async def view_manifest(
    manifest_url: Annotated[str, Field(description="Full IIIF manifest URL (e.g. 'https://lbiiif.riksarkivet.se/sdhk!85/manifest').")],
    ctx: Context,
    highlight_term: Annotated[str | None, Field(description="Optional search term to highlight.")] = None,
    max_pages: Annotated[int, Field(description="Maximum pages to load.", le=20)] = 20,
    document_info: Annotated[str | None, Field(description="Optional markdown-formatted document metadata for the info panel. Overrides the manifest label if provided.")] = None,
) -> ToolResult:
    """View document pages from a IIIF manifest URL."""
    try:
        resolved = await manifest_resolve_document(manifest_url, max_pages)
    except (ValueError, LookupError) as e:
        return error_result(str(e))
    except Exception as e:
        logger.error("view_manifest: failed to resolve manifest: %s", e)
        return error_result(f"Error resolving manifest: {e}")

    has_ui = ctx.client_supports_extension(UI_EXTENSION_ID)
    summary = build_summary(
        len(resolved.image_urls),
        resolved.page_numbers,
        has_ui,
        resolved.image_urls,
    )

    view_id = str(uuid4())
    state = ViewerState(
        view_id=view_id,
        image_urls=resolved.image_urls,
        text_layer_urls=resolved.text_layer_urls,
        page_numbers=resolved.page_numbers,
        document_info=document_info or resolved.document_info,
        highlight_term=highlight_term or "",
        reference_code="",
    )
    sc = await put_state(state)

    logger.info("view_manifest: %s, resolved %d page(s), view_id=%s", manifest_url, len(resolved.image_urls), view_id)
    return ToolResult(
        content=[types.TextContent(type="text", text=summary)],
        structured_content=sc,
    )
```

The only changes are:
1. New `document_info` parameter with default `None`
2. Line `document_info=document_info or resolved.document_info,` instead of `document_info=resolved.document_info,`

- [ ] **Step 2: Verify existing viewer tests still pass**

Run: `cd /home/morgan/ra-mcp && uv run pytest packages/viewer-mcp/tests/ -v`
Expected: All existing tests pass (new param is optional, backwards-compatible)

- [ ] **Step 3: Commit**

```bash
git add packages/viewer-mcp/src/ra_mcp_viewer_mcp/tools.py
git commit -m "feat(viewer-mcp): add optional document_info parameter to view_manifest"
```

---

### Task 4: Add view_sdhk tool

**Files:**
- Create: `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/view_sdhk_tool.py`
- Modify: `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/tools.py`
- Modify: `packages/diplomatics-mcp/pyproject.toml`

- [ ] **Step 1: Add viewer-mcp dependency to diplomatics-mcp**

In `packages/diplomatics-mcp/pyproject.toml`, add `ra-mcp-viewer-mcp` to dependencies and uv sources:

```toml
[project]
name = "ra-mcp-diplomatics-mcp"
version = "0.3.0"
description = "MCP tools for SDHK and MPO medieval document search"
requires-python = ">=3.13"
license = "Apache-2.0"
dependencies = [
    "ra-mcp-diplomatics-lib",
    "ra-mcp-viewer-mcp",
    "fastmcp>=3.2.0",
]

[tool.uv.sources]
ra-mcp-diplomatics-lib = { workspace = true }
ra-mcp-viewer-mcp = { workspace = true }
```

- [ ] **Step 2: Create view_sdhk_tool.py**

Create `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/view_sdhk_tool.py`:

```python
"""MCP tool for viewing a single SDHK charter in the document viewer."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import uuid4

from fastmcp import Context
from fastmcp.server.apps import UI_EXTENSION_ID, AppConfig
from fastmcp.tools import ToolResult
from mcp import types
from pydantic import Field

from ra_mcp_diplomatics_lib import DiplomaticsSearch
from ra_mcp_diplomatics_lib.config import LANCEDB_URI
from ra_mcp_viewer_mcp.formatter import build_summary, error_result
from ra_mcp_viewer_mcp.models import ViewerState
from ra_mcp_viewer_mcp.resolve import manifest_resolve_document
from ra_mcp_viewer_mcp.state import put_state
from ra_mcp_viewer_mcp.tools import RESOURCE_URI

from .formatter import format_sdhk_info


logger = logging.getLogger("ra_mcp.diplomatics.view_sdhk")

_db = None


def _get_db():
    global _db
    if _db is None:
        import lancedb

        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_view_sdhk_tool(mcp) -> None:
    """Register the view_sdhk MCP tool."""

    @mcp.tool(
        name="view_sdhk",
        tags={"diplomatics", "sdhk", "viewer"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "View a digitized SDHK charter in the document viewer with full metadata. "
            "Takes an SDHK ID (from search_sdhk results) and opens the interactive viewer "
            "with the charter images and a metadata panel showing author, date, summary, "
            "edition text, and seal descriptions. Only works for digitized charters."
        ),
        app=AppConfig(resource_uri=RESOURCE_URI),
    )
    async def view_sdhk(
        sdhk_id: Annotated[int, Field(description="SDHK charter ID (e.g. 85, 28672).")],
        ctx: Context,
        highlight_term: Annotated[str | None, Field(description="Optional search term to highlight.")] = None,
        max_pages: Annotated[int, Field(description="Maximum pages to load.", le=20)] = 20,
    ) -> ToolResult:
        """Look up SDHK record and open in viewer with full metadata."""
        try:
            db = _get_db()
            searcher = DiplomaticsSearch(db)
            row = searcher.get_sdhk_by_id(sdhk_id)
        except Exception as exc:
            logger.error("view_sdhk: DB lookup failed: %s", exc, exc_info=True)
            return error_result(f"Error looking up SDHK {sdhk_id}: {exc}")

        if row is None:
            return error_result(f"SDHK {sdhk_id} not found.")

        manifest_url = row.get("manifest_url", "")
        if not manifest_url:
            return error_result(
                f"SDHK {sdhk_id} is not digitized — no images available. "
                f"The record metadata is:\n\n{format_sdhk_info(row)}"
            )

        try:
            resolved = await manifest_resolve_document(manifest_url, max_pages)
        except (ValueError, LookupError) as exc:
            return error_result(str(exc))
        except Exception as exc:
            logger.error("view_sdhk: manifest resolution failed: %s", exc, exc_info=True)
            return error_result(f"Error resolving manifest: {exc}")

        document_info = format_sdhk_info(row)

        has_ui = ctx.client_supports_extension(UI_EXTENSION_ID)
        summary = build_summary(
            len(resolved.image_urls),
            resolved.page_numbers,
            has_ui,
            resolved.image_urls,
        )

        view_id = str(uuid4())
        state = ViewerState(
            view_id=view_id,
            image_urls=resolved.image_urls,
            text_layer_urls=resolved.text_layer_urls,
            page_numbers=resolved.page_numbers,
            document_info=document_info,
            highlight_term=highlight_term or "",
            reference_code=f"SDHK {sdhk_id}",
        )
        sc = await put_state(state)

        logger.info("view_sdhk: SDHK %d, %d page(s), view_id=%s", sdhk_id, len(resolved.image_urls), view_id)
        return ToolResult(
            content=[types.TextContent(type="text", text=summary)],
            structured_content=sc,
        )
```

- [ ] **Step 3: Register in tools.py**

Replace `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/tools.py` with:

```python
"""FastMCP server definition for diplomatics search tools."""

from fastmcp import FastMCP

from .sdhk_tool import register_sdhk_tool
from .mpo_tool import register_mpo_tool
from .view_sdhk_tool import register_view_sdhk_tool
from .view_mpo_tool import register_view_mpo_tool


diplomatics_mcp = FastMCP(
    name="ra-diplomatics-mcp",
    instructions=(
        "Search medieval Swedish documents: SDHK (44,000+ medieval charters before 1540) "
        "and MPO (23,000+ medieval parchment fragments). "
        "Use search_sdhk/search_mpo to find documents, then view_sdhk/view_mpo to open "
        "them in the interactive viewer with full metadata."
    ),
)

register_sdhk_tool(diplomatics_mcp)
register_mpo_tool(diplomatics_mcp)
register_view_sdhk_tool(diplomatics_mcp)
register_view_mpo_tool(diplomatics_mcp)
```

- [ ] **Step 4: Run `uv sync` to pick up new dependency**

Run: `cd /home/morgan/ra-mcp && uv sync`

- [ ] **Step 5: Commit**

```bash
git add packages/diplomatics-mcp/
git commit -m "feat(diplomatics-mcp): add view_sdhk tool with full metadata in viewer"
```

---

### Task 5: Add view_mpo tool

**Files:**
- Create: `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/view_mpo_tool.py`

- [ ] **Step 1: Create view_mpo_tool.py**

Create `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/view_mpo_tool.py`:

```python
"""MCP tool for viewing a single MPO parchment fragment in the document viewer."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import uuid4

from fastmcp import Context
from fastmcp.server.apps import UI_EXTENSION_ID, AppConfig
from fastmcp.tools import ToolResult
from mcp import types
from pydantic import Field

from ra_mcp_diplomatics_lib import DiplomaticsSearch
from ra_mcp_diplomatics_lib.config import LANCEDB_URI
from ra_mcp_viewer_mcp.formatter import build_summary, error_result
from ra_mcp_viewer_mcp.models import ViewerState
from ra_mcp_viewer_mcp.resolve import manifest_resolve_document
from ra_mcp_viewer_mcp.state import put_state
from ra_mcp_viewer_mcp.tools import RESOURCE_URI

from .formatter import format_mpo_info


logger = logging.getLogger("ra_mcp.diplomatics.view_mpo")

_db = None


def _get_db():
    global _db
    if _db is None:
        import lancedb

        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_view_mpo_tool(mcp) -> None:
    """Register the view_mpo MCP tool."""

    @mcp.tool(
        name="view_mpo",
        tags={"diplomatics", "mpo", "viewer"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "View an MPO parchment fragment in the document viewer with full codicological metadata. "
            "Takes an MPO ID (from search_mpo results) and opens the interactive viewer "
            "with the fragment images and a metadata panel showing manuscript type, dating, "
            "script, material, content, decoration, and damage descriptions."
        ),
        app=AppConfig(resource_uri=RESOURCE_URI),
    )
    async def view_mpo(
        mpo_id: Annotated[int, Field(description="MPO fragment ID (e.g. 1, 42).")],
        ctx: Context,
        highlight_term: Annotated[str | None, Field(description="Optional search term to highlight.")] = None,
        max_pages: Annotated[int, Field(description="Maximum pages to load.", le=20)] = 20,
    ) -> ToolResult:
        """Look up MPO record and open in viewer with full metadata."""
        try:
            db = _get_db()
            searcher = DiplomaticsSearch(db)
            row = searcher.get_mpo_by_id(mpo_id)
        except Exception as exc:
            logger.error("view_mpo: DB lookup failed: %s", exc, exc_info=True)
            return error_result(f"Error looking up MPO {mpo_id}: {exc}")

        if row is None:
            return error_result(f"MPO {mpo_id} not found.")

        manifest_url = row.get("manifest_url", "")
        if not manifest_url:
            return error_result(
                f"MPO {mpo_id} has no IIIF manifest — no images available. "
                f"The record metadata is:\n\n{format_mpo_info(row)}"
            )

        try:
            resolved = await manifest_resolve_document(manifest_url, max_pages)
        except (ValueError, LookupError) as exc:
            return error_result(str(exc))
        except Exception as exc:
            logger.error("view_mpo: manifest resolution failed: %s", exc, exc_info=True)
            return error_result(f"Error resolving manifest: {exc}")

        document_info = format_mpo_info(row)

        has_ui = ctx.client_supports_extension(UI_EXTENSION_ID)
        summary = build_summary(
            len(resolved.image_urls),
            resolved.page_numbers,
            has_ui,
            resolved.image_urls,
        )

        view_id = str(uuid4())
        state = ViewerState(
            view_id=view_id,
            image_urls=resolved.image_urls,
            text_layer_urls=resolved.text_layer_urls,
            page_numbers=resolved.page_numbers,
            document_info=document_info,
            highlight_term=highlight_term or "",
            reference_code=f"MPO {mpo_id}",
        )
        sc = await put_state(state)

        logger.info("view_mpo: MPO %d, %d page(s), view_id=%s", mpo_id, len(resolved.image_urls), view_id)
        return ToolResult(
            content=[types.TextContent(type="text", text=summary)],
            structured_content=sc,
        )
```

- [ ] **Step 2: Commit**

```bash
git add packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/view_mpo_tool.py
git commit -m "feat(diplomatics-mcp): add view_mpo tool with full metadata in viewer"
```

---

### Task 6: Update server instructions and run full tests

**Files:**
- Modify: `src/ra_mcp_server/server.py` (update instructions to reference view_sdhk/view_mpo)

- [ ] **Step 1: Update server instructions**

In `src/ra_mcp_server/server.py`, find the line:

```
- View SDHK/MPO documents → view_manifest with IIIF manifest URL from search results
```

Replace with:

```
- View SDHK charters → diplomatics:view_sdhk with SDHK ID from search results (includes full metadata)
- View MPO fragments → diplomatics:view_mpo with MPO ID from search results (includes full metadata)
```

- [ ] **Step 2: Run all diplomatics tests**

Run: `cd /home/morgan/ra-mcp && uv run pytest packages/diplomatics-lib/tests/ packages/diplomatics-mcp/tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Run lint and format**

Run: `cd /home/morgan/ra-mcp && uv run ruff format packages/diplomatics-lib packages/diplomatics-mcp && uv run ruff check --fix packages/diplomatics-lib packages/diplomatics-mcp`
Expected: Clean

- [ ] **Step 4: Commit**

```bash
git add src/ra_mcp_server/server.py
git commit -m "docs: update server instructions to reference view_sdhk/view_mpo tools"
```

---

## Task Summary

| Task | What | Files |
|------|------|-------|
| 1 | `get_sdhk_by_id` / `get_mpo_by_id` lookup methods | search_operations.py |
| 2 | `format_sdhk_info` / `format_mpo_info` markdown formatters | formatter.py |
| 3 | `document_info` param on `view_manifest` | viewer-mcp tools.py |
| 4 | `view_sdhk` tool | view_sdhk_tool.py, tools.py, pyproject.toml |
| 5 | `view_mpo` tool | view_mpo_tool.py |
| 6 | Server instructions update + full test run | server.py |

# SBL MCP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add MCP search for Svenskt biografiskt lexikon (SBL) — ~9,400 biographical articles from Riksarkivet, using LanceDB full-text search.

**Architecture:** Two workspace packages (`sbl-lib` for models/ingest/search, `sbl-mcp` for MCP tool/formatter) plus an ingest script. Mirrors the diplomatics package pattern exactly.

**Tech Stack:** pydantic, lancedb, pyarrow, fastmcp==3.1.1

---

### Task 1: Create sbl-lib package scaffolding

**Files:**
- Create: `packages/sbl-lib/pyproject.toml`
- Create: `packages/sbl-lib/src/ra_mcp_sbl_lib/__init__.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ra_mcp_sbl_lib"]

[project]
name = "ra-mcp-sbl-lib"
version = "0.11.3"
description = "Svenskt biografiskt lexikon (SBL) search via LanceDB"
requires-python = ">=3.13"
license = "Apache-2.0"
dependencies = [
    "ra-mcp-common",
    "lancedb>=0.20,<1",
    "pyarrow>=18,<20",
    "pydantic>=2,<3",
]

[tool.uv.sources]
ra-mcp-common = { workspace = true }
```

**Step 2: Create __init__.py**

```python
"""Svenskt biografiskt lexikon (SBL) search via LanceDB."""

__version__ = "0.11.3"

from .search_operations import SBLSearch

__all__ = ["SBLSearch"]
```

---

### Task 2: Create SBLRecord model with tests

**Files:**
- Create: `packages/sbl-lib/src/ra_mcp_sbl_lib/models.py`
- Create: `packages/sbl-lib/src/ra_mcp_sbl_lib/config.py`
- Create: `packages/sbl-lib/tests/__init__.py` (empty)
- Create: `packages/sbl-lib/tests/test_models.py`

**Step 1: Create config.py**

```python
"""Configuration for SBL search."""

import os


LANCEDB_URI = os.getenv("SBL_LANCEDB_URI", "hf://datasets/carpelan/sbl-lance")

SBL_TABLE = "sbl"

DEFAULT_LIMIT = 25
MAX_LIMIT = 100
```

**Step 2: Create models.py**

CSV columns (exact headers from the file):
- `Article id` → article_id (int)
- `Svenskt biografiskt lexikon (SBL): URI` → sbl_uri (str)
- `Type of article` → article_type (str)
- `SBL volume number` → volume_number (str)
- `Page number in volume` → page_number (str)
- `Surname` → surname (str)
- `Given name` → given_name (str)
- `Gender` → gender (str)
- `Occupation, royal title, rank` → occupation (str)
- `Prefix to year of birth` → birth_year_prefix (str)
- `Year of birth` → birth_year (int | None)
- `Month of birth` → birth_month (int | None)
- `Day of birth` → birth_day (int | None)
- `Place of birth` → birth_place (str)
- `Comment on place of birth` → birth_place_comment (str)
- `Place of birth (physical location)` → birth_place_physical (str)
- `Prefix to year of death` → death_year_prefix (str)
- `Year of death` → death_year (int | None)
- `Month of death` → death_month (int | None)
- `Day of death` → death_day (int | None)
- `Place of death` → death_place (str)
- `Comment on place of death` → death_place_comment (str)
- `Place of death (physical location)` → death_place_physical (str)
- `Id of main article` → main_article_id (str)
- `Curriculum vitae` → cv (str)
- `Archive` → archive (str)
- `Printed works` → printed_works (str)
- `Sources` → sources (str)
- `Article author` → article_author (str)
- `Image file 1..9` → image_files (list[str]) — collected into a list
- `Image 1..9 description` → image_descriptions (list[str]) — collected into a list

NULL sentinel in CSV means empty — map to "" or None.

```python
"""Pydantic model for SBL biographical records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _clean(value: str | None) -> str:
    """Return empty string for NULL or None values."""
    if value is None or value == "NULL":
        return ""
    return value.strip()


def _parse_int(value: str | None) -> int | None:
    """Parse an integer from a CSV value, returning None for empty/NULL."""
    cleaned = _clean(value)
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


class SBLRecord(BaseModel):
    """A record from Svenskt biografiskt lexikon (Swedish Biographical Lexicon)."""

    model_config = ConfigDict(populate_by_name=True)

    article_id: int
    sbl_uri: str = ""
    article_type: str = ""
    volume_number: str = ""
    page_number: str = ""
    surname: str = ""
    given_name: str = ""
    gender: str = ""
    occupation: str = ""
    birth_year_prefix: str = ""
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    birth_place: str = ""
    birth_place_comment: str = ""
    birth_place_physical: str = ""
    death_year_prefix: str = ""
    death_year: int | None = None
    death_month: int | None = None
    death_day: int | None = None
    death_place: str = ""
    death_place_comment: str = ""
    death_place_physical: str = ""
    main_article_id: str = ""
    cv: str = ""
    archive: str = ""
    printed_works: str = ""
    sources: str = ""
    article_author: str = ""
    image_files: list[str] = []
    image_descriptions: list[str] = []

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "SBLRecord":
        """Construct an SBLRecord from a raw CSV row dict."""
        image_files = []
        image_descriptions = []
        for i in range(1, 10):
            img = _clean(row.get(f"Image file {i}", ""))
            desc = _clean(row.get(f"Image {i} description", ""))
            if img:
                image_files.append(img)
                image_descriptions.append(desc)

        return cls(
            article_id=int(row["Article id"]),
            sbl_uri=_clean(row.get("Svenskt biografiskt lexikon (SBL): URI")),
            article_type=_clean(row.get("Type of article")),
            volume_number=_clean(row.get("SBL volume number")),
            page_number=_clean(row.get("Page number in volume")),
            surname=_clean(row.get("Surname")),
            given_name=_clean(row.get("Given name")),
            gender=_clean(row.get("Gender")),
            occupation=_clean(row.get("Occupation, royal title, rank")),
            birth_year_prefix=_clean(row.get("Prefix to year of birth")),
            birth_year=_parse_int(row.get("Year of birth")),
            birth_month=_parse_int(row.get("Month of birth")),
            birth_day=_parse_int(row.get("Day of birth")),
            birth_place=_clean(row.get("Place of birth")),
            birth_place_comment=_clean(row.get("Comment on place of birth")),
            birth_place_physical=_clean(row.get("Place of birth (physical location)")),
            death_year_prefix=_clean(row.get("Prefix to year of death")),
            death_year=_parse_int(row.get("Year of death")),
            death_month=_parse_int(row.get("Month of death")),
            death_day=_parse_int(row.get("Day of death")),
            death_place=_clean(row.get("Place of death")),
            death_place_comment=_clean(row.get("Comment on place of death")),
            death_place_physical=_clean(row.get("Place of death (physical location)")),
            main_article_id=_clean(row.get("Id of main article")),
            cv=_clean(row.get("Curriculum vitae")),
            archive=_clean(row.get("Archive")),
            printed_works=_clean(row.get("Printed works")),
            sources=_clean(row.get("Sources")),
            article_author=_clean(row.get("Article author")),
            image_files=image_files,
            image_descriptions=image_descriptions,
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.surname,
            self.given_name,
            self.occupation,
            self.cv,
            self.birth_place,
            self.death_place,
            self.archive,
            self.printed_works,
            self.sources,
        ]
        return " ".join(p for p in parts if p)
```

**Step 3: Write test_models.py**

```python
"""Tests for SBLRecord pydantic model."""

import pytest

from ra_mcp_sbl_lib.models import SBLRecord, _clean, _parse_int


SBL_CSV_ROW: dict[str, str] = {
    "Article id": "5491",
    "Svenskt biografiskt lexikon (SBL): URI": "https://sok.riksarkivet.se/sbl/Presentation.aspx?id=5491",
    "Type of article": "Person article",
    "SBL volume number": "1",
    "Page number in volume": "5",
    "Surname": "Abelin",
    "Given name": "Gustaf R",
    "Gender": "m",
    "Occupation, royal title, rank": "Arméofficer, Lantförsvarsminister",
    "Prefix to year of birth": "",
    "Year of birth": "1819",
    "Month of birth": "5",
    "Day of birth": "17",
    "Place of birth": "Linköpings Domkyrkoförsamling",
    "Comment on place of birth": "",
    "Place of birth (physical location)": "NULL",
    "Prefix to year of death": "",
    "Year of death": "1903",
    "Month of death": "9",
    "Day of death": "19",
    "Place of death": "Kvillinge församling",
    "Comment on place of death": "på Björnsnäs",
    "Place of death (physical location)": "NULL",
    "Id of main article": "NULL",
    "Curriculum vitae": "Gustaf Rudolf Abelin, f. 17 maj 1819 i Linköping",
    "Archive": "",
    "Printed works": "Några upplysningar angående milis-systemet",
    "Sources": "Militaria: ansökn. och meritförteckn., RA",
    "Article author": "S. Drakenberg.",
    "Image file 1": "https://sok.riksarkivet.se/sbl/bilder/5491_7_001_00000006_0.jpg",
    "Image 1 description": "O. R. Abelin. Fotografi.",
    "Image file 2": "NULL",
    "Image 2 description": "NULL",
    "Image file 3": "NULL",
    "Image 3 description": "NULL",
    "Image file 4": "NULL",
    "Image 4 description": "NULL",
    "Image file 5": "NULL",
    "Image 5 description": "NULL",
    "Image file 6": "NULL",
    "Image 6 description": "NULL",
    "Image file 7": "NULL",
    "Image 7 description": "NULL",
    "Image file 8": "NULL",
    "Image 8 description": "NULL",
    "Image file 9": "NULL",
    "Image 9 description": "NULL",
}

FAMILY_ARTICLE_ROW: dict[str, str] = {
    "Article id": "5490",
    "Svenskt biografiskt lexikon (SBL): URI": "https://sok.riksarkivet.se/sbl/Presentation.aspx?id=5490",
    "Type of article": "Family article",
    "SBL volume number": "1",
    "Page number in volume": "1",
    "Surname": "Abelin",
    "Given name": "släkt",
    "Gender": "-",
    "Occupation, royal title, rank": "NULL",
    "Prefix to year of birth": "",
    "Year of birth": "",
    "Month of birth": "NULL",
    "Day of birth": "NULL",
    "Place of birth": "NULL",
    "Comment on place of birth": "NULL",
    "Place of birth (physical location)": "NULL",
    "Prefix to year of death": "",
    "Year of death": "",
    "Month of death": "NULL",
    "Day of death": "NULL",
    "Place of death": "NULL",
    "Comment on place of death": "NULL",
    "Place of death (physical location)": "NULL",
    "Id of main article": "NULL",
    "Curriculum vitae": "",
    "Archive": "",
    "Printed works": "",
    "Sources": "",
    "Article author": "",
    "Image file 1": "NULL",
    "Image 1 description": "NULL",
    **{f"Image file {i}": "NULL" for i in range(2, 10)},
    **{f"Image {i} description": "NULL" for i in range(2, 10)},
}


def test_sbl_from_csv_row_basic_fields() -> None:
    record = SBLRecord.from_csv_row(SBL_CSV_ROW)
    assert record.article_id == 5491
    assert record.surname == "Abelin"
    assert record.given_name == "Gustaf R"
    assert record.gender == "m"
    assert record.occupation == "Arméofficer, Lantförsvarsminister"


def test_sbl_from_csv_row_dates() -> None:
    record = SBLRecord.from_csv_row(SBL_CSV_ROW)
    assert record.birth_year == 1819
    assert record.birth_month == 5
    assert record.birth_day == 17
    assert record.death_year == 1903
    assert record.death_month == 9
    assert record.death_day == 19


def test_sbl_from_csv_row_places() -> None:
    record = SBLRecord.from_csv_row(SBL_CSV_ROW)
    assert record.birth_place == "Linköpings Domkyrkoförsamling"
    assert record.death_place == "Kvillinge församling"
    assert record.death_place_comment == "på Björnsnäs"


def test_sbl_null_values_become_empty() -> None:
    record = SBLRecord.from_csv_row(SBL_CSV_ROW)
    assert record.birth_place_physical == ""
    assert record.death_place_physical == ""
    assert record.main_article_id == ""


def test_sbl_family_article_no_dates() -> None:
    record = SBLRecord.from_csv_row(FAMILY_ARTICLE_ROW)
    assert record.article_type == "Family article"
    assert record.gender == "-"
    assert record.birth_year is None
    assert record.death_year is None
    assert record.occupation == ""


def test_sbl_images_collected() -> None:
    record = SBLRecord.from_csv_row(SBL_CSV_ROW)
    assert len(record.image_files) == 1
    assert record.image_files[0] == "https://sok.riksarkivet.se/sbl/bilder/5491_7_001_00000006_0.jpg"
    assert record.image_descriptions[0] == "O. R. Abelin. Fotografi."


def test_sbl_images_empty_for_family_article() -> None:
    record = SBLRecord.from_csv_row(FAMILY_ARTICLE_ROW)
    assert record.image_files == []
    assert record.image_descriptions == []


def test_sbl_searchable_text_includes_key_fields() -> None:
    record = SBLRecord.from_csv_row(SBL_CSV_ROW)
    text = record.searchable_text
    assert "Abelin" in text
    assert "Gustaf R" in text
    assert "Arméofficer" in text
    assert "Linköpings" in text
    assert "Kvillinge" in text


def test_sbl_searchable_text_empty_fields_omitted() -> None:
    record = SBLRecord.from_csv_row(FAMILY_ARTICLE_ROW)
    text = record.searchable_text
    assert text == "Abelin släkt"


def test_sbl_uri() -> None:
    record = SBLRecord.from_csv_row(SBL_CSV_ROW)
    assert record.sbl_uri == "https://sok.riksarkivet.se/sbl/Presentation.aspx?id=5491"


@pytest.mark.parametrize("value,expected", [
    pytest.param("NULL", "", id="null-sentinel"),
    pytest.param(None, "", id="none"),
    pytest.param("  hello  ", "hello", id="whitespace"),
    pytest.param("", "", id="empty"),
])
def test_clean(value, expected) -> None:
    assert _clean(value) == expected


@pytest.mark.parametrize("value,expected", [
    pytest.param("1819", 1819, id="normal-int"),
    pytest.param("NULL", None, id="null"),
    pytest.param("", None, id="empty"),
    pytest.param(None, None, id="none"),
    pytest.param("0000", 0, id="zero-year"),
])
def test_parse_int(value, expected) -> None:
    assert _parse_int(value) == expected
```

**Step 4: Run tests**

Run: `uv run pytest packages/sbl-lib/tests/test_models.py -v`

**Step 5: Commit**

```
feat(sbl-lib): add SBLRecord model with CSV parsing and tests
```

---

### Task 3: Create test fixture and ingest module with tests

**Files:**
- Create: `packages/sbl-lib/tests/fixtures/sbl_sample.csv`
- Create: `packages/sbl-lib/src/ra_mcp_sbl_lib/ingest.py`
- Create: `packages/sbl-lib/tests/test_ingest.py`

**Step 1: Create sbl_sample.csv**

Extract 5 rows from the real CSV at `/tmp/sbl.csv` — pick rows with varying data:
- One family article (id 5490, no dates/CV)
- Three person articles with CV content (ids 5491, 5492, 5493)
- One medieval person (id 5495, year 0000/1410)

Truncate CV fields to ~200 chars to keep fixture small. Use the real CSV headers exactly.

**Step 2: Create ingest.py**

Follow `packages/diplomatics-lib/src/ra_mcp_diplomatics_lib/ingest.py` pattern exactly:

```python
"""CSV ingest for SBL records into LanceDB."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .config import SBL_TABLE
from .models import SBLRecord

if TYPE_CHECKING:
    import lancedb

logger = logging.getLogger(__name__)


def ingest_sbl(db: "lancedb.DBConnection", csv_path: str | Path) -> "lancedb.table.Table":
    """Ingest SBL CSV into a LanceDB table with FTS index.

    Args:
        db: LanceDB database connection.
        csv_path: Path to the SBL CSV file (semicolon-delimited, latin-1 encoded).

    Returns:
        The created LanceDB table.

    Raises:
        ValueError: If no records could be parsed from the CSV.
    """
    csv_path = Path(csv_path)
    records: list[dict] = []

    with csv_path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for lineno, row in enumerate(reader, start=2):
            try:
                record = SBLRecord.from_csv_row(row)
            except Exception as exc:
                logger.warning("Skipping SBL row %d: %s", lineno, exc)
                continue
            flat = record.model_dump()
            flat["searchable_text"] = record.searchable_text
            records.append(flat)

    if not records:
        raise ValueError(f"No valid SBL records parsed from {csv_path}")

    logger.info("Parsed %d SBL records", len(records))

    table = db.create_table(SBL_TABLE, data=records, mode="overwrite")
    table.create_fts_index("searchable_text", replace=True)
    return table
```

**Step 3: Write test_ingest.py**

```python
"""Tests for SBL CSV ingest into LanceDB."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_sbl_lib.ingest import ingest_sbl

FIXTURES = Path(__file__).parent / "fixtures"
SBL_FIXTURE = FIXTURES / "sbl_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_sbl(db):
    table = ingest_sbl(db, SBL_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_sbl_columns(db):
    table = ingest_sbl(db, SBL_FIXTURE)
    schema_names = table.schema.names
    for col in ("article_id", "surname", "cv", "searchable_text", "gender", "birth_year", "death_year"):
        assert col in schema_names, f"Missing column: {col}"
```

**Step 4: Run tests**

Run: `uv run pytest packages/sbl-lib/tests/test_ingest.py -v`

**Step 5: Commit**

```
feat(sbl-lib): add CSV ingest into LanceDB with FTS index
```

---

### Task 4: Create search operations with tests

**Files:**
- Create: `packages/sbl-lib/src/ra_mcp_sbl_lib/search_operations.py`
- Create: `packages/sbl-lib/tests/test_search_operations.py`

**Step 1: Create search_operations.py**

Follow `packages/diplomatics-lib/src/ra_mcp_diplomatics_lib/search_operations.py` pattern. Key differences from diplomatics:
- Single table (sbl) instead of two (sdhk/mpo)
- More filters: gender (exact), occupation/birth_place/death_place (substring), year ranges
- Year range filters use integer comparison on birth_year/death_year fields

```python
"""Full-text search operations over SBL LanceDB table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import SBL_TABLE

if TYPE_CHECKING:
    import lancedb


@dataclass
class SearchResult:
    """Result from an SBL search query."""

    records: list[dict]
    total_hits: int
    keyword: str
    offset: int
    limit: int


class SBLSearch:
    """Search operations over the SBL LanceDB table."""

    def __init__(self, db: "lancedb.DBConnection") -> None:
        self._db = db

    def search(
        self,
        keyword: str,
        *,
        limit: int = 25,
        offset: int = 0,
        gender: str | None = None,
        occupation: str | None = None,
        birth_place: str | None = None,
        death_place: str | None = None,
        birth_year_min: int | None = None,
        birth_year_max: int | None = None,
        death_year_min: int | None = None,
        death_year_max: int | None = None,
    ) -> SearchResult:
        """Search the SBL table using full-text search with optional filters.

        Args:
            keyword: Search term (required, non-empty).
            limit: Maximum number of results to return.
            offset: Number of results to skip (for pagination).
            gender: Optional exact match on gender (m/f/-).
            occupation: Optional case-insensitive substring filter on occupation.
            birth_place: Optional case-insensitive substring filter on birth place.
            death_place: Optional case-insensitive substring filter on death place.
            birth_year_min: Optional minimum birth year (inclusive).
            birth_year_max: Optional maximum birth year (inclusive).
            death_year_min: Optional minimum death year (inclusive).
            death_year_max: Optional maximum death year (inclusive).

        Returns:
            SearchResult with matching records.

        Raises:
            ValueError: If keyword is empty.
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be non-empty")

        has_filters = any([gender, occupation, birth_place, death_place, birth_year_min, birth_year_max, death_year_min, death_year_max])
        fetch_limit = (limit + offset) * 10 if has_filters else limit + offset

        table = self._db.open_table(SBL_TABLE)
        rows = (
            table.search(keyword, query_type="fts")
            .limit(fetch_limit)
            .to_list()
        )

        # Apply post-filters
        if gender:
            rows = [r for r in rows if r.get("gender", "") == gender]
        if occupation:
            occupation_lower = occupation.lower()
            rows = [r for r in rows if occupation_lower in r.get("occupation", "").lower()]
        if birth_place:
            birth_place_lower = birth_place.lower()
            rows = [r for r in rows if birth_place_lower in r.get("birth_place", "").lower()]
        if death_place:
            death_place_lower = death_place.lower()
            rows = [r for r in rows if death_place_lower in r.get("death_place", "").lower()]
        if birth_year_min is not None:
            rows = [r for r in rows if r.get("birth_year") is not None and r["birth_year"] >= birth_year_min]
        if birth_year_max is not None:
            rows = [r for r in rows if r.get("birth_year") is not None and r["birth_year"] <= birth_year_max]
        if death_year_min is not None:
            rows = [r for r in rows if r.get("death_year") is not None and r["death_year"] >= death_year_min]
        if death_year_max is not None:
            rows = [r for r in rows if r.get("death_year") is not None and r["death_year"] <= death_year_max]

        total_hits = len(rows)
        page = rows[offset : offset + limit]

        return SearchResult(
            records=page,
            total_hits=total_hits,
            keyword=keyword,
            offset=offset,
            limit=limit,
        )
```

**Step 2: Write test_search_operations.py**

```python
"""Tests for SBLSearch over ingested sample data."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_sbl_lib.ingest import ingest_sbl
from ra_mcp_sbl_lib.search_operations import SBLSearch

FIXTURES = Path(__file__).parent / "fixtures"
SBL_FIXTURE = FIXTURES / "sbl_sample.csv"


@pytest.fixture
def search(tmp_path):
    """Return an SBLSearch backed by ingested sample data."""
    db = lancedb.connect(str(tmp_path / "test.lance"))
    ingest_sbl(db, SBL_FIXTURE)
    return SBLSearch(db)


def test_search_returns_results(search):
    result = search.search("Abelin")
    assert result.total_hits >= 1
    assert len(result.records) >= 1


def test_search_empty_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search("")


def test_search_whitespace_keyword_raises(search):
    with pytest.raises(ValueError):
        search.search("   ")


def test_search_pagination(search):
    result = search.search("Abelin", limit=2)
    assert len(result.records) <= 2
    assert result.limit == 2


def test_search_result_fields(search):
    result = search.search("Abelin")
    assert result.keyword == "Abelin"
    assert result.offset == 0
    assert result.limit == 25


def test_search_has_searchable_text(search):
    result = search.search("Abelin")
    assert result.records
    assert "searchable_text" in result.records[0]
```

**Step 3: Run tests**

Run: `uv run pytest packages/sbl-lib/tests/test_search_operations.py -v`

**Step 4: Commit**

```
feat(sbl-lib): add SBLSearch with FTS and post-filters
```

---

### Task 5: Create sbl-mcp package with tool and formatter

**Files:**
- Create: `packages/sbl-mcp/pyproject.toml`
- Create: `packages/sbl-mcp/src/ra_mcp_sbl_mcp/__init__.py`
- Create: `packages/sbl-mcp/src/ra_mcp_sbl_mcp/tools.py`
- Create: `packages/sbl-mcp/src/ra_mcp_sbl_mcp/sbl_tool.py`
- Create: `packages/sbl-mcp/src/ra_mcp_sbl_mcp/formatter.py`
- Create: `packages/sbl-mcp/src/ra_mcp_sbl_mcp/server.py`
- Create: `packages/sbl-mcp/tests/__init__.py` (empty)
- Create: `packages/sbl-mcp/tests/test_tools.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ra_mcp_sbl_mcp"]

[project]
name = "ra-mcp-sbl-mcp"
version = "0.11.3"
description = "MCP tools for Svenskt biografiskt lexikon (SBL) search"
requires-python = ">=3.13"
license = "Apache-2.0"
dependencies = [
    "ra-mcp-sbl-lib",
    "fastmcp==3.1.1",
]

[tool.uv.sources]
ra-mcp-sbl-lib = { workspace = true }
```

**Step 2: Create __init__.py**

```python
"""MCP tools for Svenskt biografiskt lexikon (SBL) search."""

__version__ = "0.11.3"

from .tools import sbl_mcp

__all__ = ["sbl_mcp"]
```

**Step 3: Create tools.py**

```python
"""FastMCP server definition for SBL search tool."""

from fastmcp import FastMCP

from .sbl_tool import register_sbl_tool


sbl_mcp = FastMCP(
    name="ra-sbl-mcp",
    instructions=(
        "Search Svenskt biografiskt lexikon (SBL) — 9,400+ biographical articles "
        "about notable individuals and families in Swedish history. "
        "Covers persons from medieval times through the 20th century. "
        "Articles include biographical text, occupations, birth/death dates and places, "
        "sources, and portrait image URLs."
    ),
)

register_sbl_tool(sbl_mcp)
```

**Step 4: Create sbl_tool.py**

Follow `packages/diplomatics-mcp/src/ra_mcp_diplomatics_mcp/sdhk_tool.py` pattern:

```python
"""MCP tool for searching Svenskt biografiskt lexikon."""

from __future__ import annotations

import logging
from typing import Annotated

from pydantic import Field

from ra_mcp_sbl_lib import SBLSearch
from ra_mcp_sbl_lib.config import LANCEDB_URI

from .formatter import format_sbl_results


logger = logging.getLogger("ra_mcp.sbl.sbl_tool")

_db = None


def _get_db():
    """Return a cached LanceDB connection, opening it on first use."""
    global _db
    if _db is None:
        import lancedb

        logger.info("Opening LanceDB at %s", LANCEDB_URI)
        _db = lancedb.connect(LANCEDB_URI)
    return _db


def register_sbl_tool(mcp) -> None:
    """Register the search_sbl MCP tool with the given FastMCP server."""

    @mcp.tool(
        name="search_sbl",
        tags={"sbl", "biography", "search"},
        annotations={"readOnlyHint": True, "openWorldHint": True},
        description=(
            "Search Svenskt biografiskt lexikon (SBL) — 9,400+ biographical articles about notable people in Swedish history. "
            "Returns name, occupation, birth/death dates and places, biographical text excerpt, sources, and portrait image URLs. "
            "Covers medieval to 20th century. Articles go up to letter S (T-Ö not yet published). "
            "Filter by gender, occupation, place, or year range. "
            "Paginate with offset (0, 25, 50, ...)."
        ),
    )
    async def search_sbl(
        keyword: Annotated[
            str,
            Field(description="Search term for full-text search across SBL biographical text."),
        ],
        offset: Annotated[
            int,
            Field(description="Pagination start position. Use 0 for first page, then 25, 50, etc."),
        ] = 0,
        limit: Annotated[
            int,
            Field(description="Maximum number of records to return per query (default 25)."),
        ] = 25,
        gender: Annotated[
            str | None,
            Field(description="Optional filter: m (male), f (female), or - (family/other). Exact match."),
        ] = None,
        occupation: Annotated[
            str | None,
            Field(description="Optional filter: occupation or title (case-insensitive substring match)."),
        ] = None,
        birth_place: Annotated[
            str | None,
            Field(description="Optional filter: birth place (case-insensitive substring match)."),
        ] = None,
        death_place: Annotated[
            str | None,
            Field(description="Optional filter: death place (case-insensitive substring match)."),
        ] = None,
        birth_year_min: Annotated[
            int | None,
            Field(description="Optional filter: minimum birth year (inclusive)."),
        ] = None,
        birth_year_max: Annotated[
            int | None,
            Field(description="Optional filter: maximum birth year (inclusive)."),
        ] = None,
        death_year_min: Annotated[
            int | None,
            Field(description="Optional filter: minimum death year (inclusive)."),
        ] = None,
        death_year_max: Annotated[
            int | None,
            Field(description="Optional filter: maximum death year (inclusive)."),
        ] = None,
        research_context: Annotated[
            str | None,
            Field(description="Brief summary of the user's research goal. Used for logging only."),
        ] = None,
    ) -> str:
        """Search SBL biographical articles using full-text search."""
        if not keyword or not keyword.strip():
            return "Error: keyword must not be empty. Provide a search term, e.g. 'läkare'."

        if research_context:
            logger.info("search_sbl | context: %s", research_context)
        logger.info("search_sbl called with keyword='%s', offset=%d, limit=%d", keyword, offset, limit)

        try:
            db = _get_db()
            searcher = SBLSearch(db)
            result = searcher.search(
                keyword,
                limit=limit,
                offset=offset,
                gender=gender,
                occupation=occupation,
                birth_place=birth_place,
                death_place=death_place,
                birth_year_min=birth_year_min,
                birth_year_max=birth_year_max,
                death_year_min=death_year_min,
                death_year_max=death_year_max,
            )
            return format_sbl_results(result)

        except Exception as exc:
            logger.error("search_sbl failed: %s: %s", type(exc).__name__, exc, exc_info=True)
            return f"Error: SBL search failed — {exc!s}"
```

**Step 5: Create formatter.py**

```python
"""Plain-text formatter for SBL search results."""

from __future__ import annotations

from ra_mcp_sbl_lib.search_operations import SearchResult


def _format_date(year: int | None, month: int | None, day: int | None, prefix: str = "") -> str:
    """Format a date from components, returning empty string if no year."""
    if year is None:
        return ""
    parts = [prefix, str(year)] if prefix else [str(year)]
    if month is not None:
        parts.append(f"-{month:02d}")
        if day is not None:
            parts.append(f"-{day:02d}")
    return "".join(parts)


def format_sbl_results(result: SearchResult) -> str:
    """Format SBL search results as plain text for MCP/LLM consumption."""
    if not result.records:
        if result.offset > 0:
            return (
                f"No more SBL results for '{result.keyword}' at offset {result.offset}. "
                f"Total found: {result.total_hits}"
            )
        return f"No SBL results found for '{result.keyword}'."

    lines: list[str] = []
    lines.append(
        f"SBL search results for '{result.keyword}': "
        f"showing {len(result.records)} of {result.total_hits} records "
        f"(offset {result.offset})"
    )
    lines.append("")

    for rec in result.records:
        article_id = rec.get("article_id", "")
        lines.append(f"--- SBL {article_id} ---")

        surname = rec.get("surname", "")
        given_name = rec.get("given_name", "")
        name = f"{given_name} {surname}".strip() if given_name else surname
        if name:
            lines.append(f"Name: {name}")

        gender = rec.get("gender", "")
        if gender and gender != "-":
            lines.append(f"Gender: {gender}")

        article_type = rec.get("article_type", "")
        if article_type == "Family article":
            lines.append("Type: Family article")

        occupation = rec.get("occupation", "")
        if occupation:
            lines.append(f"Occupation: {occupation}")

        born = _format_date(rec.get("birth_year"), rec.get("birth_month"), rec.get("birth_day"), rec.get("birth_year_prefix", ""))
        birth_place = rec.get("birth_place", "")
        if born or birth_place:
            parts = [p for p in [born, birth_place] if p]
            lines.append(f"Born: {', '.join(parts)}")

        died = _format_date(rec.get("death_year"), rec.get("death_month"), rec.get("death_day"), rec.get("death_year_prefix", ""))
        death_place = rec.get("death_place", "")
        if died or death_place:
            parts = [p for p in [died, death_place] if p]
            lines.append(f"Died: {', '.join(parts)}")

        cv = rec.get("cv", "")
        if cv:
            truncated = cv[:500] + "..." if len(cv) > 500 else cv
            lines.append(f"CV: {truncated}")

        sources = rec.get("sources", "")
        if sources:
            truncated = sources[:300] + "..." if len(sources) > 300 else sources
            lines.append(f"Sources: {truncated}")

        sbl_uri = rec.get("sbl_uri", "")
        if sbl_uri:
            lines.append(f"SBL: {sbl_uri}")

        image_files = rec.get("image_files", [])
        if image_files:
            lines.append(f"Portrait: {image_files[0]}")

        lines.append("")

    next_offset = result.offset + result.limit
    if next_offset < result.total_hits:
        lines.append(
            f"More results available. Use offset={next_offset} to see the next page."
        )

    return "\n".join(lines)
```

**Step 6: Create server.py**

```python
"""Standalone dev server for SBL MCP."""

import argparse
import os

from .tools import sbl_mcp


def main():
    parser = argparse.ArgumentParser(description="SBL MCP Server")
    parser.add_argument("--stdio", action="store_true")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3004")))
    args = parser.parse_args()
    if args.stdio:
        sbl_mcp.run(transport="stdio")
    else:
        sbl_mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port, path="/mcp")


if __name__ == "__main__":
    main()
```

**Step 7: Create test_tools.py**

```python
"""Tests for SBL MCP server."""

from ra_mcp_sbl_mcp import sbl_mcp


def test_sbl_mcp_server_name():
    assert sbl_mcp.name == "ra-sbl-mcp"
```

**Step 8: Run tests**

Run: `uv run pytest packages/sbl-mcp/tests/ packages/sbl-lib/tests/ -v`

**Step 9: Commit**

```
feat(sbl-mcp): add search_sbl MCP tool with formatter
```

---

### Task 6: Create ingest script

**Files:**
- Create: `scripts/ingest_sbl.py`

**Step 1: Create ingest_sbl.py**

Follow `scripts/ingest_diplomatics.py` pattern:

```python
"""Download and ingest SBL CSV into LanceDB.

Usage:
    uv run python scripts/ingest_sbl.py [--sbl PATH] [--output PATH]

By default, downloads the CSV from Riksarkivet and ingests it.
Use --sbl to provide a local file instead.
"""

import argparse
import logging
import tempfile
from pathlib import Path
from urllib.request import urlopen

import lancedb

from ra_mcp_sbl_lib.ingest import ingest_sbl

DEFAULT_OUTPUT = Path("data/sbl")
SBL_CSV_URL = "https://filer.riksarkivet.se/registerdata/SBL/csv/SBL_2023.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def download_sbl(dest: Path) -> Path:
    """Download SBL CSV from Riksarkivet."""
    logger.info("Downloading SBL from %s ...", SBL_CSV_URL)
    with urlopen(SBL_CSV_URL) as resp:
        dest.write_bytes(resp.read())
    logger.info("Saved SBL CSV to %s (%d bytes)", dest, dest.stat().st_size)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and ingest SBL into LanceDB")
    parser.add_argument("--sbl", type=Path, default=None, help="Local SBL CSV path (skips download)")
    parser.add_argument("--output", type=Path, default=None, help="LanceDB output path")
    args = parser.parse_args()

    output_path = args.output or DEFAULT_OUTPUT
    output_path.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(output_path)

    with tempfile.TemporaryDirectory() as tmp:
        sbl_path = args.sbl
        if sbl_path is None:
            sbl_path = Path(tmp) / "sbl.csv"
            download_sbl(sbl_path)

        print(f"Ingesting SBL from {sbl_path} ...")
        sbl_table = ingest_sbl(db, sbl_path)
        print(f"  → {sbl_table.count_rows()} rows")

    print(f"\nDone! Table at: {output_path}")


if __name__ == "__main__":
    main()
```

**Step 2: Test locally with the already-downloaded CSV**

Run: `uv run python scripts/ingest_sbl.py --sbl /tmp/sbl.csv --output /tmp/sbl-lance`
Expected: `→ 9406 rows` (or close)

**Step 3: Commit**

```
feat(sbl): add ingest script for SBL CSV to LanceDB
```

---

### Task 7: Register in root server and workspace

**Files:**
- Modify: `src/ra_mcp_server/server.py` — add optional SBL import (same pattern as diplomatics at lines 73-82)
- Modify: `pyproject.toml` — add `sbl = ["ra-mcp-sbl-mcp"]` to optional-dependencies, add workspace sources for `ra-mcp-sbl-lib` and `ra-mcp-sbl-mcp`

**Step 1: Add to server.py** after the diplomatics block (~line 82):

```python
# sbl-mcp is optional (requires lancedb which has limited platform wheels)
try:
    from ra_mcp_sbl_mcp import sbl_mcp  # ty: ignore[unresolved-import]

    AVAILABLE_MODULES["sbl"] = {
        "server": sbl_mcp,
        "description": "Search Svenskt biografiskt lexikon (Swedish Biographical Lexicon)",
        "default": True,
    }
except ImportError:
    pass
```

**Step 2: Update root pyproject.toml**

Add under `[project.optional-dependencies]`:
```toml
sbl = ["ra-mcp-sbl-mcp"]
```

Add under `[tool.uv.sources]`:
```toml
ra-mcp-sbl-lib = { workspace = true }
ra-mcp-sbl-mcp = { workspace = true }
```

Add to `[tool.ruff.lint.isort]` known-first-party list:
```
"ra_mcp_sbl_lib", "ra_mcp_sbl_mcp"
```

**Step 3: Update server instructions** in `build_instructions()` to mention SBL:

Add to TOOL SELECTION section:
```
- Biographical lookup → sbl:search_sbl with name or keyword
```

Add to COVERAGE section:
```
- SBL: 9,400+ biographical articles (sbl:search_sbl) — notable Swedish individuals, medieval to 20th century
```

**Step 4: Run uv sync**

Run: `uv sync`

**Step 5: Run all tests**

Run: `uv run pytest packages/sbl-lib/tests/ packages/sbl-mcp/tests/ -v`

**Step 6: Run lint**

Run: `uv run ruff check packages/sbl-lib/ packages/sbl-mcp/ scripts/ingest_sbl.py`

**Step 7: Commit**

```
feat(sbl): register SBL module in root server and workspace
```

---

### Task 8: End-to-end test with real data

**Step 1: Ingest from local CSV**

Run: `uv run python scripts/ingest_sbl.py --sbl /tmp/sbl.csv --output /tmp/sbl-lance`

**Step 2: Test search via standalone server**

Run: `SBL_LANCEDB_URI=/tmp/sbl-lance uv run python -m ra_mcp_sbl_mcp.server --port 3004`

Test with curl or MCP inspector.

**Step 3: Verify all tests pass**

Run: `uv run pytest packages/sbl-lib/tests/ packages/sbl-mcp/tests/ -v`

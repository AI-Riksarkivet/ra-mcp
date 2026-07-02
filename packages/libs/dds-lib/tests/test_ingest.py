"""Tests for DDS CSV ingest into LanceDB."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_dds_lib.ingest import ingest_doda, ingest_fodelse, ingest_vigsel


FIXTURES = Path(__file__).parent / "fixtures"
FODELSE_FIXTURE_DIR = FIXTURES / "fodda"
DODA_FIXTURE_DIR = FIXTURES / "doda"
VIGSEL_FIXTURE_DIR = FIXTURES / "vigslar"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


# ---------------------------------------------------------------------------
# Födelse ingest
# ---------------------------------------------------------------------------


def test_ingest_fodelse(db):
    table = ingest_fodelse(db, FODELSE_FIXTURE_DIR)
    assert table.count_rows() == 5


def test_ingest_fodelse_columns(db):
    table = ingest_fodelse(db, FODELSE_FIXTURE_DIR)
    schema_names = table.schema.names
    for col in ("forsamling", "lan", "fornamn", "far_fornamn", "far_efternamn", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


# ---------------------------------------------------------------------------
# Döda ingest
# ---------------------------------------------------------------------------


def test_ingest_doda(db):
    table = ingest_doda(db, DODA_FIXTURE_DIR)
    assert table.count_rows() == 5


def test_ingest_doda_columns(db):
    table = ingest_doda(db, DODA_FIXTURE_DIR)
    schema_names = table.schema.names
    for col in ("forsamling", "fornamn", "efternamn", "dodsorsak", "dodsorsak_klassificerat", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


# ---------------------------------------------------------------------------
# Vigsel ingest
# ---------------------------------------------------------------------------


def test_ingest_vigsel(db):
    table = ingest_vigsel(db, VIGSEL_FIXTURE_DIR)
    assert table.count_rows() == 5


def test_ingest_vigsel_columns(db):
    table = ingest_vigsel(db, VIGSEL_FIXTURE_DIR)
    schema_names = table.schema.names
    for col in (
        "brudgum_fornamn",
        "brudgum_efternamn",
        "brud_fornamn",
        "brud_efternamn",
        "brud_alder",
        "searchable_text",
    ):
        assert col in schema_names, f"Missing column: {col}"

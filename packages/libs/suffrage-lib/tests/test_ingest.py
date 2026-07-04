"""Tests for Suffrage CSV ingest into LanceDB."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_suffrage_lib.ingest import ingest_fkpr, ingest_rostratt


FIXTURES = Path(__file__).parent / "fixtures"
ROSTRATT_FIXTURE_DIR = FIXTURES / "rostratt"
FKPR_FIXTURE = FIXTURES / "fkpr_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_rostratt(db):
    table = ingest_rostratt(db, ROSTRATT_FIXTURE_DIR)
    assert table.count_rows() == 5


def test_ingest_rostratt_columns(db):
    table = ingest_rostratt(db, ROSTRATT_FIXTURE_DIR)
    schema_names = table.schema.names
    for col in ("lan", "fornamn", "efternamn", "yrke", "ortens_namn", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_fkpr(db):
    table = ingest_fkpr(db, FKPR_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_fkpr_columns(db):
    table = ingest_fkpr(db, FKPR_FIXTURE)
    schema_names = table.schema.names
    for col in ("efternamn", "foernamn", "titel_yrke", "membership_years", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"

"""Tests for Wincars CSV ingest into LanceDB."""

from __future__ import annotations

from pathlib import Path

import lancedb
import pytest

from ra_mcp_wincars_lib.ingest import ingest_wincars


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_wincars(db):
    table = ingest_wincars(db, FIXTURES)
    assert table.count_rows() == 5


def test_ingest_wincars_columns(db):
    table = ingest_wincars(db, FIXTURES)
    schema_names = table.schema.names
    for col in ("nreg", "typ", "fabrikat", "hemvist", "cnr", "mnr", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_wincars_no_csv_raises(db, tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="No CSV files found"):
        ingest_wincars(db, empty_dir)

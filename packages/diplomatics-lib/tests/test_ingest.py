"""Tests for CSV ingest into LanceDB."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_diplomatics_lib.ingest import ingest_mpo, ingest_sdhk

FIXTURES = Path(__file__).parent / "fixtures"
SDHK_FIXTURE = FIXTURES / "sdhk_sample.csv"
MPO_FIXTURE = FIXTURES / "mpo_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_sdhk(db):
    table = ingest_sdhk(db, SDHK_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_mpo(db):
    table = ingest_mpo(db, MPO_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_sdhk_columns(db):
    table = ingest_sdhk(db, SDHK_FIXTURE)
    schema_names = table.schema.names
    for col in ("id", "summary", "author", "searchable_text", "manifest_url"):
        assert col in schema_names, f"Missing column: {col}"


def test_ingest_mpo_columns(db):
    table = ingest_mpo(db, MPO_FIXTURE)
    schema_names = table.schema.names
    for col in ("id", "content", "category", "searchable_text", "manifest_url"):
        assert col in schema_names, f"Missing column: {col}"

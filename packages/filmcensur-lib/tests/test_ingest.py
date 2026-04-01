"""Tests for Filmcensur CSV ingest into LanceDB."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_filmcensur_lib.ingest import ingest_filmreg


FIXTURES = Path(__file__).parent / "fixtures"
FILMREG_FIXTURE = FIXTURES / "filmreg_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_filmreg(db):
    table = ingest_filmreg(db, FILMREG_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_filmreg_columns(db):
    table = ingest_filmreg(db, FILMREG_FIXTURE)
    schema_names = table.schema.names
    for col in ("granskningsnummer", "titel_org", "titel_svensk", "filmkategori", "searchable_text", "produktionsland", "aaldersgraens"):
        assert col in schema_names, f"Missing column: {col}"

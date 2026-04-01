"""Tests for Fältjägare CSV ingest into LanceDB."""

from pathlib import Path

import lancedb
import pytest

from ra_mcp_faltjagare_lib.ingest import ingest_faltjagare


FIXTURES = Path(__file__).parent / "fixtures"
FALTJAGARE_FIXTURE = FIXTURES / "faltjagare_sample.csv"


@pytest.fixture
def db(tmp_path):
    return lancedb.connect(str(tmp_path / "test.lance"))


def test_ingest_faltjagare(db):
    table = ingest_faltjagare(db, FALTJAGARE_FIXTURE)
    assert table.count_rows() == 5


def test_ingest_faltjagare_columns(db):
    table = ingest_faltjagare(db, FALTJAGARE_FIXTURE)
    schema_names = table.schema.names
    for col in ("soldatnamn", "foernamn", "familjenamn", "kompani", "befattning", "rotens_socken", "region", "searchable_text"):
        assert col in schema_names, f"Missing column: {col}"

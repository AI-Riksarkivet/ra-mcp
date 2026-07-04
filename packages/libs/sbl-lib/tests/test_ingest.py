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
